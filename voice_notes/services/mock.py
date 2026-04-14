"""
Mock transcription service for testing.

Provides deterministic responses without calling external APIs.
Useful for:
- Unit testing without API keys
- Integration tests
- Local development
"""
from typing import BinaryIO, Set, Optional
from .base import TranscriptionService, TranscriptionResult, TranscriptionError


class MockTranscriptionService(TranscriptionService):
    """
    Mock transcription service for testing.

    Can be configured to:
    - Return a specific transcript
    - Simulate failures
    - Track call counts

    Example:
        service = MockTranscriptionService(transcript="Test transcript")
        result = service.transcribe(audio_file, "test.mp3")
        assert result.text == "Test transcript"
        assert service.call_count == 1

        # Simulate failure
        failing_service = MockTranscriptionService(should_fail=True)
        with pytest.raises(TranscriptionError):
            failing_service.transcribe(audio_file, "test.mp3")
    """

    def __init__(
        self,
        transcript: str = "This is a mock transcript for testing purposes.",
        duration_seconds: float = 10.0,
        language: str = "en",
        should_fail: bool = False,
        fail_message: str = "Mock transcription failure",
        fail_retriable: bool = True
    ):
        """
        Initialize mock service.

        Args:
            transcript: Text to return on successful transcription
            duration_seconds: Duration to report
            language: Language code to report
            should_fail: If True, transcribe() raises TranscriptionError
            fail_message: Error message when failing
            fail_retriable: Whether simulated failure is retriable
        """
        self._transcript = transcript
        self._duration = duration_seconds
        self._language = language
        self._should_fail = should_fail
        self._fail_message = fail_message
        self._fail_retriable = fail_retriable
        self.call_count = 0
        self.last_filename: Optional[str] = None

    @property
    def name(self) -> str:
        return "Mock Transcription Service"

    @property
    def supported_formats(self) -> Set[str]:
        return {'.mp3', '.wav', '.m4a', '.webm', '.mp4', '.ogg'}

    @property
    def max_file_size_bytes(self) -> int:
        return 25 * 1024 * 1024  # 25MB like OpenAI

    def transcribe(self, audio_file: BinaryIO, filename: str) -> TranscriptionResult:
        """
        Mock transcription - returns configured response or raises error.
        """
        self.call_count += 1
        self.last_filename = filename

        self._log_transcription_start(filename, 0)

        if self._should_fail:
            self._log_transcription_error(filename, Exception(self._fail_message))
            raise TranscriptionError(
                self._fail_message,
                retriable=self._fail_retriable
            )

        result = TranscriptionResult(
            text=self._transcript,
            duration_seconds=self._duration,
            language=self._language
        )

        self._log_transcription_success(filename, self._duration)
        return result

    def reset(self) -> None:
        """Reset call tracking for test isolation."""
        self.call_count = 0
        self.last_filename = None

    def configure_success(self, transcript: str, duration: float = 10.0) -> None:
        """Configure for successful response."""
        self._should_fail = False
        self._transcript = transcript
        self._duration = duration

    def configure_failure(self, message: str, retriable: bool = True) -> None:
        """Configure to simulate failure."""
        self._should_fail = True
        self._fail_message = message
        self._fail_retriable = retriable
