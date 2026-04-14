"""
Tests for transcription service abstraction.

These tests verify:
1. Service interface contract
2. Mock service behavior
3. OpenAI service (with mocked API)
4. Service factory
"""
import io
from unittest.mock import Mock, patch
from django.test import TestCase, override_settings

from voice_notes.services.base import (
    TranscriptionService,
    TranscriptionResult,
    TranscriptionError
)
from voice_notes.services.mock import MockTranscriptionService
from voice_notes.services.factory import get_transcription_service


class TranscriptionServiceContractTests:
    """
    Contract tests that ANY TranscriptionService implementation must pass.

    Subclass this for each provider to ensure consistent behavior.
    """

    def get_service(self) -> TranscriptionService:
        """Return the service instance to test. Override in subclass."""
        raise NotImplementedError

    def test_service_has_name(self):
        """Service must have a human-readable name."""
        service = self.get_service()
        self.assertIsInstance(service.name, str)
        self.assertGreater(len(service.name), 0)

    def test_service_has_supported_formats(self):
        """Service must declare supported formats as set of extensions."""
        service = self.get_service()
        self.assertIsInstance(service.supported_formats, set)
        self.assertGreater(len(service.supported_formats), 0)
        # All formats should be lowercase with dot prefix
        for fmt in service.supported_formats:
            self.assertTrue(fmt.startswith('.'), f"Format {fmt} should start with '.'")
            self.assertEqual(fmt, fmt.lower(), f"Format {fmt} should be lowercase")

    def test_service_has_max_file_size(self):
        """Service must declare maximum file size."""
        service = self.get_service()
        self.assertIsInstance(service.max_file_size_bytes, int)
        self.assertGreater(service.max_file_size_bytes, 0)

    def test_validate_file_rejects_unsupported_format(self):
        """Service should reject unsupported file formats."""
        service = self.get_service()
        with self.assertRaises(TranscriptionError) as ctx:
            service.validate_file("test.xyz", 1000)
        self.assertFalse(ctx.exception.retriable)
        self.assertIn("unsupported", ctx.exception.message.lower())

    def test_validate_file_rejects_oversized_file(self):
        """Service should reject files exceeding size limit."""
        service = self.get_service()
        huge_size = service.max_file_size_bytes + 1
        with self.assertRaises(TranscriptionError) as ctx:
            service.validate_file("test.mp3", huge_size)
        self.assertFalse(ctx.exception.retriable)
        self.assertIn("large", ctx.exception.message.lower())

    def test_validate_file_accepts_valid_file(self):
        """Service should accept valid files without raising."""
        service = self.get_service()
        # Pick first supported format
        fmt = list(service.supported_formats)[0]
        # Should not raise
        service.validate_file(f"test{fmt}", 1000)


class MockTranscriptionServiceTests(TranscriptionServiceContractTests, TestCase):
    """Test MockTranscriptionService implementation."""

    def get_service(self):
        return MockTranscriptionService()

    def test_transcribe_returns_configured_text(self):
        """Mock service returns configured transcript."""
        service = MockTranscriptionService(
            transcript="Custom transcript",
            duration_seconds=15.5
        )

        result = service.transcribe(io.BytesIO(b"fake audio"), "test.mp3")

        self.assertEqual(result.text, "Custom transcript")
        self.assertEqual(result.duration_seconds, 15.5)

    def test_transcribe_tracks_call_count(self):
        """Mock service tracks number of calls."""
        service = MockTranscriptionService()
        self.assertEqual(service.call_count, 0)

        service.transcribe(io.BytesIO(b"audio1"), "test1.mp3")
        self.assertEqual(service.call_count, 1)

        service.transcribe(io.BytesIO(b"audio2"), "test2.mp3")
        self.assertEqual(service.call_count, 2)

    def test_transcribe_tracks_last_filename(self):
        """Mock service tracks last filename processed."""
        service = MockTranscriptionService()

        service.transcribe(io.BytesIO(b"audio"), "my_audio.mp3")

        self.assertEqual(service.last_filename, "my_audio.mp3")

    def test_transcribe_can_simulate_failure(self):
        """Mock service can simulate transcription failure."""
        service = MockTranscriptionService(
            should_fail=True,
            fail_message="Simulated API error",
            fail_retriable=True
        )

        with self.assertRaises(TranscriptionError) as ctx:
            service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertEqual(ctx.exception.message, "Simulated API error")
        self.assertTrue(ctx.exception.retriable)

    def test_transcribe_can_simulate_permanent_failure(self):
        """Mock service can simulate non-retriable failure."""
        service = MockTranscriptionService(
            should_fail=True,
            fail_message="Invalid audio",
            fail_retriable=False
        )

        with self.assertRaises(TranscriptionError) as ctx:
            service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertFalse(ctx.exception.retriable)

    def test_reset_clears_tracking(self):
        """Reset clears call tracking."""
        service = MockTranscriptionService()
        service.transcribe(io.BytesIO(b"audio"), "test.mp3")
        self.assertEqual(service.call_count, 1)

        service.reset()

        self.assertEqual(service.call_count, 0)
        self.assertIsNone(service.last_filename)

    def test_configure_success_changes_behavior(self):
        """Configure success updates response."""
        service = MockTranscriptionService(should_fail=True)

        service.configure_success("New transcript", duration=20.0)
        result = service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertEqual(result.text, "New transcript")
        self.assertEqual(result.duration_seconds, 20.0)

    def test_configure_failure_changes_behavior(self):
        """Configure failure updates error response."""
        service = MockTranscriptionService()

        service.configure_failure("New error", retriable=False)

        with self.assertRaises(TranscriptionError) as ctx:
            service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertEqual(ctx.exception.message, "New error")
        self.assertFalse(ctx.exception.retriable)


class OpenAIWhisperServiceTests(TranscriptionServiceContractTests, TestCase):
    """Test OpenAI Whisper service with mocked API."""

    def get_service(self):
        from voice_notes.services.openai_whisper import OpenAIWhisperService
        return OpenAIWhisperService()

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('voice_notes.services.openai_whisper._get_openai_client')
    def test_transcribe_success(self, mock_get_client):
        """Successful transcription returns result."""
        mock_client = Mock()
        mock_client.audio.transcriptions.create.return_value = Mock(
            text="Hello world",
            duration=5.0,
            language="en"
        )
        mock_get_client.return_value = mock_client

        service = self.get_service()
        result = service.transcribe(io.BytesIO(b"fake audio"), "test.mp3")

        self.assertEqual(result.text, "Hello world")
        self.assertEqual(result.duration_seconds, 5.0)
        self.assertEqual(result.language, "en")

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('voice_notes.services.openai_whisper._get_openai_client')
    def test_transcribe_connection_error_is_retriable(self, mock_get_client):
        """Connection errors should be retriable."""
        import openai
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = \
            openai.APIConnectionError(request=Mock())
        mock_get_client.return_value = mock_client

        service = self.get_service()
        with self.assertRaises(TranscriptionError) as ctx:
            service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertTrue(ctx.exception.retriable)

    @override_settings(OPENAI_API_KEY='test-key')
    @patch('voice_notes.services.openai_whisper._get_openai_client')
    def test_transcribe_rate_limit_is_retriable(self, mock_get_client):
        """Rate limit errors should be retriable."""
        import openai
        mock_client = Mock()
        mock_client.audio.transcriptions.create.side_effect = \
            openai.RateLimitError("Rate limited", response=Mock(), body=None)
        mock_get_client.return_value = mock_client

        service = self.get_service()
        with self.assertRaises(TranscriptionError) as ctx:
            service.transcribe(io.BytesIO(b"audio"), "test.mp3")

        self.assertTrue(ctx.exception.retriable)


class ServiceFactoryTests(TestCase):
    """Test service factory function."""

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock')
    def test_factory_returns_mock_service(self):
        """Factory returns MockTranscriptionService for 'mock' provider."""
        service = get_transcription_service()
        self.assertIsInstance(service, MockTranscriptionService)

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='openai')
    def test_factory_returns_openai_service(self):
        """Factory returns OpenAIWhisperService for 'openai' provider."""
        from voice_notes.services.openai_whisper import OpenAIWhisperService
        service = get_transcription_service()
        self.assertIsInstance(service, OpenAIWhisperService)

    @override_settings(VOICE_NOTE_TRANSCRIPTION_PROVIDER='unknown')
    def test_factory_raises_for_unknown_provider(self):
        """Factory raises TranscriptionError for unknown provider."""
        with self.assertRaises(TranscriptionError) as ctx:
            get_transcription_service()

        self.assertIn("unknown", ctx.exception.message.lower())
        self.assertFalse(ctx.exception.retriable)

    @override_settings(
        VOICE_NOTE_TRANSCRIPTION_PROVIDER='mock',
        VOICE_NOTE_MOCK_TRANSCRIPT='Custom mock transcript'
    )
    def test_factory_configures_mock_transcript(self):
        """Factory configures mock transcript from settings."""
        service = get_transcription_service()
        result = service.transcribe(io.BytesIO(b"audio"), "test.mp3")
        self.assertEqual(result.text, "Custom mock transcript")


class TranscriptionResultTests(TestCase):
    """Test TranscriptionResult dataclass."""

    def test_result_is_immutable(self):
        """TranscriptionResult should be immutable (frozen)."""
        result = TranscriptionResult(text="Test", duration_seconds=10.0)

        with self.assertRaises(AttributeError):
            result.text = "Modified"

    def test_result_defaults(self):
        """TranscriptionResult has sensible defaults."""
        result = TranscriptionResult(text="Test")

        self.assertEqual(result.text, "Test")
        self.assertIsNone(result.duration_seconds)
        self.assertIsNone(result.confidence)
        self.assertIsNone(result.language)


class TranscriptionErrorTests(TestCase):
    """Test TranscriptionError exception."""

    def test_error_stores_message(self):
        """Error stores message attribute."""
        error = TranscriptionError("Test error")
        self.assertEqual(error.message, "Test error")

    def test_error_default_retriable(self):
        """Error is retriable by default."""
        error = TranscriptionError("Test error")
        self.assertTrue(error.retriable)

    def test_error_can_be_non_retriable(self):
        """Error can be marked as non-retriable."""
        error = TranscriptionError("Permanent failure", retriable=False)
        self.assertFalse(error.retriable)

    def test_error_str_includes_retry_status(self):
        """Error string representation includes retry status."""
        retriable = TranscriptionError("Error 1", retriable=True)
        permanent = TranscriptionError("Error 2", retriable=False)

        self.assertIn("retriable", str(retriable))
        self.assertIn("permanent", str(permanent))
