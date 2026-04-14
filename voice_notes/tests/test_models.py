"""
Tests for VoiceNote model.

These tests verify:
1. Model creation and defaults
2. Status transitions
3. File handling
4. Relationships
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError as DjangoValidationError

from bookings.models import Booking
from accommodations.models import Apartment
from voice_notes.models import VoiceNote


class VoiceNoteModelTests(TestCase):
    """Test VoiceNote model behavior."""

    @classmethod
    def setUpTestData(cls):
        """Create shared test data."""
        cls.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        cls.booking = Booking.objects.create(
            accommodation=cls.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )

    def test_create_voice_note_minimal(self):
        """Voice note can be created with minimal fields."""
        audio = SimpleUploadedFile(
            "test.mp3",
            b"fake audio content",
            content_type="audio/mpeg"
        )
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertIsNotNone(voice_note.id)
        self.assertEqual(voice_note.status, VoiceNote.Status.PENDING)
        self.assertEqual(voice_note.transcript, '')
        self.assertIsNone(voice_note.audio_duration_seconds)

    def test_default_status_is_pending(self):
        """New voice notes default to pending status."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertEqual(voice_note.status, VoiceNote.Status.PENDING)

    def test_status_choices(self):
        """All expected status choices exist."""
        choices = [c[0] for c in VoiceNote.Status.choices]

        self.assertIn('pending', choices)
        self.assertIn('processing', choices)
        self.assertIn('completed', choices)
        self.assertIn('failed', choices)

    def test_transcript_can_be_updated(self):
        """Transcript field can be set after creation."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        voice_note.transcript = "This is the transcribed text."
        voice_note.status = VoiceNote.Status.COMPLETED
        voice_note.save()

        voice_note.refresh_from_db()
        self.assertEqual(voice_note.transcript, "This is the transcribed text.")
        self.assertEqual(voice_note.status, VoiceNote.Status.COMPLETED)

    def test_error_message_stored_on_failure(self):
        """Failed transcriptions store error message."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        voice_note.status = VoiceNote.Status.FAILED
        voice_note.error_message = "API rate limit exceeded"
        voice_note.save()

        voice_note.refresh_from_db()
        self.assertEqual(voice_note.status, VoiceNote.Status.FAILED)
        self.assertEqual(voice_note.error_message, "API rate limit exceeded")

    def test_audio_duration_can_be_set(self):
        """Audio duration is stored as integer seconds."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio,
            audio_duration_seconds=45
        )

        self.assertEqual(voice_note.audio_duration_seconds, 45)

    def test_voice_note_belongs_to_booking(self):
        """Voice note has foreign key to booking."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertEqual(voice_note.booking, self.booking)
        self.assertEqual(voice_note.booking_id, self.booking.id)

    def test_booking_can_have_multiple_voice_notes(self):
        """A booking can have multiple voice notes."""
        for i in range(3):
            audio = SimpleUploadedFile(f"test{i}.mp3", b"audio", content_type="audio/mpeg")
            VoiceNote.objects.create(
                booking=self.booking,
                audio_file=audio
            )

        self.assertEqual(self.booking.voice_notes.count(), 3)

    def test_timestamps_auto_set(self):
        """Created and updated timestamps are automatically set."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertIsNotNone(voice_note.created_at)
        self.assertIsNotNone(voice_note.updated_at)

    def test_transcribed_at_initially_none(self):
        """Transcribed timestamp is None for new voice notes."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertIsNone(voice_note.transcribed_at)

    def test_file_size_stored(self):
        """Audio file size is stored."""
        content = b"x" * 1000
        audio = SimpleUploadedFile("test.mp3", content, content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio,
            audio_file_size=len(content)
        )

        self.assertEqual(voice_note.audio_file_size, 1000)

    def test_created_by_optional(self):
        """Created by field is optional."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        self.assertEqual(voice_note.created_by, '')

    def test_created_by_can_be_set(self):
        """Created by field stores identifier."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio,
            created_by="user_123"
        )

        self.assertEqual(voice_note.created_by, "user_123")

    def test_str_representation(self):
        """Voice note has meaningful string representation."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )

        str_repr = str(voice_note)
        self.assertIn(str(self.booking.id), str_repr)

    def test_delete_voice_note_keeps_booking(self):
        """Deleting voice note doesn't delete booking."""
        audio = SimpleUploadedFile("test.mp3", b"audio", content_type="audio/mpeg")
        voice_note = VoiceNote.objects.create(
            booking=self.booking,
            audio_file=audio
        )
        booking_id = self.booking.id

        voice_note.delete()

        self.assertTrue(Booking.objects.filter(id=booking_id).exists())


class VoiceNoteQueryTests(TestCase):
    """Test VoiceNote querysets and filtering."""

    @classmethod
    def setUpTestData(cls):
        cls.apartment = Apartment.objects.create(
            name="Test Apartment",
            price=100.00,
            location="Test City",
            bedrooms=2
        )
        cls.booking = Booking.objects.create(
            accommodation=cls.apartment,
            guest_name="Test Guest",
            start_date="2024-06-01",
            end_date="2024-06-05"
        )

    def test_filter_by_status(self):
        """Voice notes can be filtered by status."""
        for status in ['pending', 'processing', 'completed', 'failed']:
            audio = SimpleUploadedFile(f"{status}.mp3", b"audio", content_type="audio/mpeg")
            VoiceNote.objects.create(
                booking=self.booking,
                audio_file=audio,
                status=status
            )

        pending = VoiceNote.objects.filter(status=VoiceNote.Status.PENDING)
        completed = VoiceNote.objects.filter(status=VoiceNote.Status.COMPLETED)

        self.assertEqual(pending.count(), 1)
        self.assertEqual(completed.count(), 1)

    def test_filter_by_booking(self):
        """Voice notes can be filtered by booking."""
        booking2 = Booking.objects.create(
            accommodation=self.apartment,
            guest_name="Other Guest",
            start_date="2024-07-01",
            end_date="2024-07-05"
        )

        audio1 = SimpleUploadedFile("test1.mp3", b"audio", content_type="audio/mpeg")
        audio2 = SimpleUploadedFile("test2.mp3", b"audio", content_type="audio/mpeg")
        VoiceNote.objects.create(booking=self.booking, audio_file=audio1)
        VoiceNote.objects.create(booking=booking2, audio_file=audio2)

        notes_for_booking1 = VoiceNote.objects.filter(booking=self.booking)
        self.assertEqual(notes_for_booking1.count(), 1)
