from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


def voice_note_upload_path(instance, filename):
    """Generate upload path: voice_notes/booking_{id}/{filename}"""
    return f"voice_notes/booking_{instance.booking_id}/{filename}"


class VoiceNote(models.Model):
    """
    Voice note attached to a booking.

    Supports both synchronous and asynchronous transcription based on audio duration.
    Short clips (<= threshold) are processed synchronously for immediate feedback.
    Longer clips are queued for background processing.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    # Relationships
    booking = models.ForeignKey(
        'bookings.Booking',
        on_delete=models.CASCADE,
        related_name='voice_notes'
    )

    # Audio file
    audio_file = models.FileField(
        upload_to=voice_note_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'm4a', 'webm', 'mp4', 'ogg'])
        ]
    )
    audio_duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duration in seconds"
    )
    audio_file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )

    # Transcription
    transcript = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    error_message = models.TextField(
        blank=True,
        default='',
        help_text="Error details if transcription failed"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transcribed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Staff identifier who created the note"
    )

    class Meta:
        db_table = 'voice_note'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['booking', '-created_at'], name='voice_note_booking_idx'),
            models.Index(fields=['status'], name='voice_note_status_idx'),
        ]

    def __str__(self):
        return f"VoiceNote {self.id} for Booking {self.booking_id} ({self.status})"

    @property
    def is_processed(self) -> bool:
        """Check if transcription is complete (success or failure)"""
        return self.status in (self.Status.COMPLETED, self.Status.FAILED)

    @property
    def is_retriable(self) -> bool:
        """Check if failed transcription can be retried"""
        return self.status == self.Status.FAILED

    def mark_processing(self) -> None:
        """Mark as currently being processed"""
        self.status = self.Status.PROCESSING
        self.error_message = ''
        self.save(update_fields=['status', 'error_message', 'updated_at'])

    def mark_completed(self, transcript: str, duration: float = None) -> None:
        """Mark as successfully transcribed"""
        from django.utils import timezone
        self.status = self.Status.COMPLETED
        self.transcript = transcript
        self.transcribed_at = timezone.now()
        if duration:
            self.audio_duration_seconds = int(duration)
        self.save(update_fields=[
            'status', 'transcript', 'transcribed_at',
            'audio_duration_seconds', 'updated_at'
        ])

    def mark_failed(self, error_message: str) -> None:
        """Mark as failed with error details"""
        self.status = self.Status.FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message', 'updated_at'])
