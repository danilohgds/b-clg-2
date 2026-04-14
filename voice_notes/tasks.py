"""
Celery tasks for asynchronous voice note processing.

These tasks handle background transcription for longer audio files,
keeping the API responsive while heavy processing happens in workers.
"""
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute between retries
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,  # Max 5 minutes between retries
)
def transcribe_voice_note_async(self, voice_note_id: int) -> dict:
    """
    Asynchronously transcribe a voice note.

    This task is used for longer audio files that would cause
    request timeouts if processed synchronously.

    Args:
        voice_note_id: ID of the VoiceNote to transcribe

    Returns:
        dict with status and transcript preview

    Raises:
        Retries on retriable errors, fails permanently otherwise
    """
    from voice_notes.models import VoiceNote
    from voice_notes.services import get_transcription_service, TranscriptionError

    logger.info(f"Starting async transcription for VoiceNote {voice_note_id}")

    try:
        voice_note = VoiceNote.objects.get(id=voice_note_id)
    except VoiceNote.DoesNotExist:
        logger.error(f"VoiceNote {voice_note_id} not found")
        return {"status": "error", "message": "Voice note not found"}

    # Skip if already processed
    if voice_note.is_processed:
        logger.info(f"VoiceNote {voice_note_id} already processed, skipping")
        return {"status": "skipped", "message": "Already processed"}

    # Mark as processing
    voice_note.mark_processing()

    try:
        service = get_transcription_service()

        # Open and transcribe
        with voice_note.audio_file.open('rb') as audio_file:
            result = service.transcribe(
                audio_file,
                voice_note.audio_file.name
            )

        # Mark completed
        voice_note.mark_completed(
            transcript=result.text,
            duration=result.duration_seconds
        )

        logger.info(
            f"Async transcription complete for VoiceNote {voice_note_id}: "
            f"{len(result.text)} chars"
        )

        return {
            "status": "completed",
            "voice_note_id": voice_note_id,
            "transcript_preview": result.text[:100] + "..." if len(result.text) > 100 else result.text
        }

    except TranscriptionError as e:
        if e.retriable and self.request.retries < self.max_retries:
            logger.warning(
                f"Retriable error for VoiceNote {voice_note_id}, "
                f"retry {self.request.retries + 1}/{self.max_retries}: {e}"
            )
            # Reset status to pending for retry
            voice_note.status = VoiceNote.Status.PENDING
            voice_note.save(update_fields=['status'])
            raise self.retry(exc=e)
        else:
            logger.error(f"Permanent failure for VoiceNote {voice_note_id}: {e}")
            voice_note.mark_failed(str(e))
            return {
                "status": "failed",
                "voice_note_id": voice_note_id,
                "error": str(e)
            }

    except Exception as e:
        logger.exception(f"Unexpected error transcribing VoiceNote {voice_note_id}")
        voice_note.mark_failed(f"Unexpected error: {e}")
        return {
            "status": "failed",
            "voice_note_id": voice_note_id,
            "error": str(e)
        }
