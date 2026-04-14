"""
OpenAI Whisper API implementation for transcription.

Uses OpenAI's Whisper model via their API for high-accuracy transcription.
Requires OPENAI_API_KEY environment variable.
"""
from typing import BinaryIO, Set
from django.conf import settings
from .base import TranscriptionService, TranscriptionResult, TranscriptionError

# Import openai at module level for proper exception handling
try:
    import openai
except ImportError:
    openai = None


def _get_openai_client():
    """Create OpenAI client with configured API key."""
    if openai is None:
        raise TranscriptionError(
            "openai package not installed. Run: pip install openai",
            retriable=False
        )

    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key:
        raise TranscriptionError(
            "OPENAI_API_KEY not configured in settings",
            retriable=False
        )

    return openai.OpenAI(api_key=api_key)


class OpenAIWhisperService(TranscriptionService):
    """
    OpenAI Whisper API transcription service.

    Features:
    - High accuracy transcription
    - Automatic language detection
    - Supports mp3, mp4, mpeg, mpga, m4a, wav, webm

    Configuration:
    - OPENAI_API_KEY: Required API key

    Pricing (as of 2024):
    - $0.006 per minute of audio
    """

    @property
    def name(self) -> str:
        return "OpenAI Whisper"

    @property
    def supported_formats(self) -> Set[str]:
        return {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg'}

    @property
    def max_file_size_bytes(self) -> int:
        # OpenAI limit is 25MB
        return 25 * 1024 * 1024

    def transcribe(self, audio_file: BinaryIO, filename: str) -> TranscriptionResult:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio_file: File-like object with audio data
            filename: Original filename for the API

        Returns:
            TranscriptionResult with transcript text

        Raises:
            TranscriptionError: On API or processing failures
        """
        self._log_transcription_start(filename, audio_file.seek(0, 2))
        audio_file.seek(0)

        try:
            client = _get_openai_client()

            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=(filename, audio_file),
                response_format="verbose_json"
            )

            result = TranscriptionResult(
                text=response.text.strip(),
                duration_seconds=getattr(response, 'duration', None),
                language=getattr(response, 'language', None)
            )

            self._log_transcription_success(filename, result.duration_seconds)
            return result

        except Exception as e:
            self._log_transcription_error(filename, e)

            # Handle specific OpenAI errors if available
            if openai is not None:
                if isinstance(e, openai.APIConnectionError):
                    raise TranscriptionError(
                        f"Failed to connect to OpenAI API: {e}",
                        retriable=True
                    )
                elif isinstance(e, openai.RateLimitError):
                    raise TranscriptionError(
                        "OpenAI API rate limit exceeded. Please try again later.",
                        retriable=True
                    )
                elif isinstance(e, openai.APIStatusError):
                    # 4xx errors are usually not retriable (bad request, invalid audio)
                    # 5xx errors are retriable (server issues)
                    retriable = e.status_code >= 500
                    raise TranscriptionError(
                        f"OpenAI API error: {e.message}",
                        retriable=retriable
                    )

            # Generic error handling
            raise TranscriptionError(
                f"Unexpected error during transcription: {e}",
                retriable=True
            )
