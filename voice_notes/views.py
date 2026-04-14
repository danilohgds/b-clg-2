"""
API views for voice notes.

Supports hybrid sync/async processing based on audio duration:
- Short clips (<= SYNC_THRESHOLD): Processed synchronously for immediate feedback
- Long clips (> SYNC_THRESHOLD): Queued for async processing, returns 202 Accepted
"""
import logging
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from bookings.models import Booking
from .models import VoiceNote
from .serializers import VoiceNoteSerializer, VoiceNoteCreateSerializer
from .services import get_transcription_service, TranscriptionError
from .utils import get_audio_duration

logger = logging.getLogger(__name__)

# Configuration
SYNC_DURATION_THRESHOLD = getattr(settings, 'VOICE_NOTE_SYNC_THRESHOLD_SECONDS', 30)
MAX_DURATION = getattr(settings, 'VOICE_NOTE_MAX_DURATION_SECONDS', 180)
MAX_FILE_SIZE = getattr(settings, 'VOICE_NOTE_MAX_FILE_SIZE_BYTES', 25 * 1024 * 1024)


class VoiceNoteListCreateView(APIView):
    """
    List voice notes for a booking or create a new one.

    POST uses hybrid sync/async processing:
    - Audio <= 30s: Synchronous (immediate response with transcript)
    - Audio > 30s: Asynchronous (returns 202, transcript processed in background)
    """
    parser_classes = [MultiPartParser]

    @extend_schema(
        summary="List voice notes for a booking",
        tags=["Voice Notes"],
        responses={200: VoiceNoteSerializer(many=True)}
    )
    def get(self, request, booking_id):
        """List all voice notes for a booking."""
        booking = get_object_or_404(Booking, pk=booking_id)
        voice_notes = VoiceNote.objects.filter(booking=booking)
        serializer = VoiceNoteSerializer(voice_notes, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create a voice note",
        description=f"""
        Upload an audio file to create a voice note with automatic transcription.

        **Processing Mode:**
        - Audio <= {SYNC_DURATION_THRESHOLD}s: Synchronous (201 Created with transcript)
        - Audio > {SYNC_DURATION_THRESHOLD}s: Asynchronous (202 Accepted, poll for transcript)

        **Limits:**
        - Max duration: {MAX_DURATION} seconds
        - Max file size: {MAX_FILE_SIZE // (1024*1024)}MB
        - Supported formats: mp3, wav, m4a, webm, mp4
        """,
        tags=["Voice Notes"],
        request=VoiceNoteCreateSerializer,
        responses={
            201: OpenApiResponse(response=VoiceNoteSerializer, description="Created with transcript (sync)"),
            202: OpenApiResponse(response=VoiceNoteSerializer, description="Accepted for processing (async)"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Booking not found"),
        }
    )
    def post(self, request, booking_id):
        """
        Create a voice note with automatic transcription.

        Uses hybrid processing based on audio duration.
        """
        # Validate booking exists
        booking = get_object_or_404(Booking, pk=booking_id)

        # Validate request
        serializer = VoiceNoteCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        audio_file = serializer.validated_data['audio_file']
        created_by = serializer.validated_data.get('created_by', '')

        # Validate file size
        if audio_file.size > MAX_FILE_SIZE:
            return Response(
                {"error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get audio duration
        try:
            duration = get_audio_duration(audio_file)
            audio_file.seek(0)  # Reset after reading
        except Exception as e:
            logger.warning(f"Could not determine audio duration: {e}")
            duration = None

        # Validate duration
        if duration and duration > MAX_DURATION:
            return Response(
                {"error": f"Audio too long ({duration:.0f}s). Maximum duration is {MAX_DURATION}s"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create voice note record
        voice_note = VoiceNote.objects.create(
            booking=booking,
            audio_file=audio_file,
            audio_file_size=audio_file.size,
            audio_duration_seconds=int(duration) if duration else None,
            created_by=created_by,
            status=VoiceNote.Status.PENDING
        )

        # Decide sync vs async based on duration
        use_async = duration and duration > SYNC_DURATION_THRESHOLD

        if use_async:
            return self._process_async(voice_note)
        else:
            return self._process_sync(voice_note)

    def _process_sync(self, voice_note: VoiceNote) -> Response:
        """Process transcription synchronously for short audio."""
        logger.info(f"Processing VoiceNote {voice_note.id} synchronously")

        voice_note.mark_processing()

        try:
            service = get_transcription_service()

            # Validate file with service
            service.validate_file(
                voice_note.audio_file.name,
                voice_note.audio_file_size or voice_note.audio_file.size
            )

            # Transcribe
            with voice_note.audio_file.open('rb') as audio_file:
                result = service.transcribe(audio_file, voice_note.audio_file.name)

            voice_note.mark_completed(
                transcript=result.text,
                duration=result.duration_seconds
            )

            return Response(
                VoiceNoteSerializer(voice_note).data,
                status=status.HTTP_201_CREATED
            )

        except TranscriptionError as e:
            logger.error(f"Transcription failed for VoiceNote {voice_note.id}: {e}")
            voice_note.mark_failed(str(e))

            # Return the voice note even on failure (audio is saved)
            return Response(
                VoiceNoteSerializer(voice_note).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.exception(f"Unexpected error processing VoiceNote {voice_note.id}")
            voice_note.mark_failed(f"Unexpected error: {e}")
            return Response(
                VoiceNoteSerializer(voice_note).data,
                status=status.HTTP_201_CREATED
            )

    def _process_async(self, voice_note: VoiceNote) -> Response:
        """Queue transcription for async processing."""
        logger.info(f"Queueing VoiceNote {voice_note.id} for async processing")

        try:
            from .tasks import transcribe_voice_note_async
            transcribe_voice_note_async.delay(voice_note.id)

            return Response(
                VoiceNoteSerializer(voice_note).data,
                status=status.HTTP_202_ACCEPTED
            )
        except Exception as e:
            # If queueing fails, fall back to sync
            logger.warning(f"Failed to queue async task, falling back to sync: {e}")
            return self._process_sync(voice_note)


class VoiceNoteDetailView(APIView):
    """Retrieve or delete a specific voice note."""

    @extend_schema(
        summary="Get voice note details",
        tags=["Voice Notes"],
        responses={200: VoiceNoteSerializer}
    )
    def get(self, request, booking_id, pk):
        """Get a specific voice note."""
        voice_note = get_object_or_404(
            VoiceNote,
            pk=pk,
            booking_id=booking_id
        )
        return Response(VoiceNoteSerializer(voice_note).data)

    @extend_schema(
        summary="Delete a voice note",
        tags=["Voice Notes"],
        responses={204: None}
    )
    def delete(self, request, booking_id, pk):
        """Delete a voice note and its audio file."""
        voice_note = get_object_or_404(
            VoiceNote,
            pk=pk,
            booking_id=booking_id
        )

        # Delete the audio file
        if voice_note.audio_file:
            voice_note.audio_file.delete(save=False)

        voice_note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VoiceNoteRetryView(APIView):
    """Retry a failed transcription."""

    @extend_schema(
        summary="Retry failed transcription",
        description="Re-attempt transcription for a voice note that previously failed.",
        tags=["Voice Notes"],
        responses={
            200: VoiceNoteSerializer,
            400: OpenApiResponse(description="Voice note is not in failed state"),
        }
    )
    def post(self, request, booking_id, pk):
        """Retry transcription for a failed voice note."""
        voice_note = get_object_or_404(
            VoiceNote,
            pk=pk,
            booking_id=booking_id
        )

        if not voice_note.is_retriable:
            return Response(
                {"error": f"Cannot retry: voice note status is '{voice_note.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine sync vs async
        duration = voice_note.audio_duration_seconds
        use_async = duration and duration > SYNC_DURATION_THRESHOLD

        if use_async:
            from .tasks import transcribe_voice_note_async
            voice_note.status = VoiceNote.Status.PENDING
            voice_note.error_message = ''
            voice_note.save()
            transcribe_voice_note_async.delay(voice_note.id)
            return Response(
                VoiceNoteSerializer(voice_note).data,
                status=status.HTTP_202_ACCEPTED
            )
        else:
            # Process synchronously
            view = VoiceNoteListCreateView()
            return view._process_sync(voice_note)
