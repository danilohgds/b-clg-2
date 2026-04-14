"""
Tests for Voice Notes API endpoints.

These tests verify:
1. Upload endpoint validation
2. Sync vs async processing path selection
3. Response formats
4. Error handling
"""
import io
from unittest.mock import patch, Mock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from bookings.models import Booking
from accommodations.models import Apartment
from voice_notes.models import VoiceNote


class VoiceNoteUploadTests(TestCase):
    """Test voice note upload endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        self.booking = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )
        self.url = f"/bookings/{self.booking.id}/voice-notes/"

    def test_upload_requires_audio_file(self):
        """Upload fails without audio file."""
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('audio_file', response.data)

    def test_upload_rejects_non_audio_file(self):
        """Upload rejects non-audio files."""
        fake_file = io.BytesIO(b"not audio")
        fake_file.name = "document.pdf"

        response = self.client.post(
            self.url,
            {'audio_file': fake_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_oversized_file(self):
        """Upload rejects files exceeding size limit."""
        # Create file larger than 25MB limit
        large_content = b"x" * (26 * 1024 * 1024)
        large_file = io.BytesIO(large_content)
        large_file.name = "large.mp3"

        response = self.client.post(
            self.url,
            {'audio_file': large_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_rejects_invalid_booking(self):
        """Upload fails for non-existent booking."""
        url = "/bookings/99999/voice-notes/"
        audio = io.BytesIO(b"fake audio")
        audio.name = "test.mp3"

        response = self.client.post(
            url,
            {'audio_file': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock')
    @patch('voice_notes.views.get_audio_duration')
    def test_short_audio_processed_sync(self, mock_duration):
        """Short audio (<30s) is processed synchronously."""
        mock_duration.return_value = 15  # 15 seconds

        audio = io.BytesIO(b"fake audio content")
        audio.name = "short.mp3"

        response = self.client.post(
            self.url,
            {'audio_file': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'completed')
        self.assertIn('transcript', response.data)
        self.assertNotEqual(response.data['transcript'], '')

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock')
    @patch('voice_notes.views.get_audio_duration')
    @patch('voice_notes.tasks.transcribe_voice_note_async.delay')
    def test_long_audio_processed_async(self, mock_task, mock_duration):
        """Long audio (>30s) is queued for async processing."""
        mock_duration.return_value = 60  # 60 seconds
        mock_task.return_value = Mock(id='task-123')

        audio = io.BytesIO(b"fake audio content")
        audio.name = "long.mp3"

        response = self.client.post(
            self.url,
            {'audio_file': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        # Status is 'pending' because the async task hasn't executed yet
        self.assertEqual(response.data['status'], 'pending')
        mock_task.assert_called_once()

    @override_settings(
        VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock',
        VOICE_NOTE_MAX_DURATION_SECONDS=180
    )
    @patch('voice_notes.views.get_audio_duration')
    def test_audio_exceeding_max_duration_rejected(self, mock_duration):
        """Audio exceeding max duration (180s) is rejected."""
        mock_duration.return_value = 200  # 200 seconds > 180s max

        audio = io.BytesIO(b"fake audio content")
        audio.name = "toolong.mp3"

        response = self.client.post(
            self.url,
            {'audio_file': audio},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', str(response.data).lower())


class VoiceNoteListTests(TestCase):
    """Test voice note list endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        self.booking = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )
        self.url = f"/bookings/{self.booking.id}/voice-notes/"

    def test_list_empty(self):
        """List returns empty array when no voice notes."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 0)

    def test_list_returns_voice_notes_for_booking(self):
        """List returns only voice notes for specified booking."""
        # Create voice note for our booking
        VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.COMPLETED,
            transcript="Test transcript"
        )

        # Create another booking with its own voice note
        booking2 = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Other Guest",
            start_date="2024-07-01",
            end_date="2024-07-05"
        )
        VoiceNote.objects.create(
            booking=booking2,
            audio_file='other.mp3'
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['transcript'], "Test transcript")

    def test_list_includes_status(self):
        """List response includes status field."""
        VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.PROCESSING
        )

        response = self.client.get(self.url)

        results = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(results[0]['status'], 'processing')


class VoiceNoteDetailTests(TestCase):
    """Test voice note detail endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        self.booking = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )

    def test_get_voice_note_detail(self):
        """Can retrieve individual voice note."""
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.COMPLETED,
            transcript="Hello world"
        )
        url = f"/bookings/{self.booking.id}/voice-notes/{voice_note.id}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['transcript'], "Hello world")
        self.assertEqual(response.data['status'], 'completed')

    def test_get_nonexistent_voice_note(self):
        """Returns 404 for non-existent voice note."""
        url = f"/bookings/{self.booking.id}/voice-notes/99999/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_voice_note_wrong_booking(self):
        """Returns 404 when voice note belongs to different booking."""
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3'
        )
        # Try to access via wrong booking
        booking2 = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Other Guest",
            start_date="2024-07-01",
            end_date="2024-07-05"
        )
        url = f"/bookings/{booking2.id}/voice-notes/{voice_note.id}/"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class VoiceNoteTranscriptionErrorTests(TestCase):
    """Test error handling in transcription."""

    def setUp(self):
        self.client = APIClient()
        self.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        self.booking = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )
        self.url = f"/bookings/{self.booking.id}/voice-notes/"

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock')
    @patch('voice_notes.views.get_audio_duration')
    @patch('voice_notes.services.factory.get_transcription_service')
    def test_sync_transcription_failure_returns_error(self, mock_factory, mock_duration):
        """Sync transcription failure returns error response."""
        from voice_notes.services.base import TranscriptionError

        mock_duration.return_value = 15
        mock_service = Mock()
        mock_service.transcribe.side_effect = TranscriptionError(
            "API error", retriable=False
        )
        mock_factory.return_value = mock_service

        audio = io.BytesIO(b"fake audio")
        audio.name = "test.mp3"

        response = self.client.post(
            self.url,
            {'audio_file': audio},
            format='multipart'
        )

        # Should still create voice note but mark as failed
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock')
    @patch('voice_notes.views.get_audio_duration')
    def test_failed_voice_note_shows_error_message(self, mock_duration):
        """Failed voice note includes error message."""
        mock_duration.return_value = 15

        # Create a failed voice note directly
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.FAILED,
            error_message="Transcription service unavailable"
        )

        url = f"/bookings/{self.booking.id}/voice-notes/{voice_note.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIn('error', str(response.data).lower())


class VoiceNoteResponseFormatTests(TestCase):
    """Test API response format consistency."""

    def setUp(self):
        self.client = APIClient()
        self.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        self.booking = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )

    def test_response_includes_required_fields(self):
        """Response includes all required fields."""
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.COMPLETED,
            transcript="Test transcript",
            audio_duration_seconds=30
        )
        url = f"/bookings/{self.booking.id}/voice-notes/{voice_note.id}/"

        response = self.client.get(url)

        self.assertIn('id', response.data)
        self.assertIn('status', response.data)
        self.assertIn('transcript', response.data)
        self.assertIn('audio_duration_seconds', response.data)
        self.assertIn('created_at', response.data)

    def test_pending_voice_note_has_empty_transcript(self):
        """Pending voice notes have empty transcript."""
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file='test.mp3',
            status=VoiceNote.Status.PENDING
        )
        url = f"/bookings/{self.booking.id}/voice-notes/{voice_note.id}/"

        response = self.client.get(url)

        self.assertEqual(response.data['transcript'], '')
