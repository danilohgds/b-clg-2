"""
Base interface for Voice-to-Text transcription services.

This module defines the contract that all transcription service implementations
must follow, enabling easy swapping of providers (OpenAI, Deepgram, local Whisper, etc.)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional, Set
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TranscriptionResult:
    """
    Immutable result from a transcription service.

    Attributes:
        text: The transcribed text
        duration_seconds: Audio duration (if provided by service)
        confidence: Confidence score 0-1 (if provided)
        language: Detected language code (e.g., 'en')
    """
    text: str
    duration_seconds: Optional[float] = None
    confidence: Optional[float] = None
    language: Optional[str] = None


class TranscriptionError(Exception):
    """
    Base exception for transcription failures.

    Attributes:
        message: Human-readable error description
        retriable: Whether the operation can be retried
            - True: Temporary failure (network, rate limit, timeout)
            - False: Permanent failure (invalid audio, unsupported format)
    """

    def __init__(self, message: str, retriable: bool = True):
        super().__init__(message)
        self.message = message
        self.retriable = retriable

    def __str__(self):
        retry_status = "retriable" if self.retriable else "permanent"
        return f"{self.message} ({retry_status})"


class TranscriptionService(ABC):
    """
    Abstract base class for voice-to-text transcription services.

    Implementations must provide:
    - name: Service identifier for logging
    - supported_formats: File extensions this service accepts
    - max_file_size_bytes: Maximum file size limit
    - transcribe(): Core transcription method

    Example usage:
        service = get_transcription_service()
        try:
            service.validate_file("audio.mp3", file_size=1024000)
            result = service.transcribe(audio_file, "audio.mp3")
            print(result.text)
        except TranscriptionError as e:
            if e.retriable:
                queue_for_retry()
            else:
                mark_permanently_failed(e.message)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable service name for logging and debugging."""
        pass

    @property
    @abstractmethod
    def supported_formats(self) -> Set[str]:
        """
        Set of supported file extensions (lowercase, with dot).
        Example: {'.mp3', '.wav', '.m4a'}
        """
        pass

    @property
    @abstractmethod
    def max_file_size_bytes(self) -> int:
        """Maximum supported file size in bytes."""
        pass

    @abstractmethod
    def transcribe(self, audio_file: BinaryIO, filename: str) -> TranscriptionResult:
        """
        Transcribe audio to text.

        Args:
            audio_file: File-like object containing audio data
            filename: Original filename (used for format detection)

        Returns:
            TranscriptionResult containing the transcript

        Raises:
            TranscriptionError: If transcription fails
                - retriable=True for temporary failures (network, rate limit)
                - retriable=False for permanent failures (invalid audio)
        """
        pass

    def validate_file(self, filename: str, file_size: int) -> None:
        """
        Validate file before attempting transcription.

        Args:
            filename: Name of the file
            file_size: Size in bytes

        Raises:
            TranscriptionError: If validation fails (always retriable=False)
        """
        ext = Path(filename).suffix.lower()

        if ext not in self.supported_formats:
            raise TranscriptionError(
                f"Unsupported audio format '{ext}'. "
                f"Supported formats: {', '.join(sorted(self.supported_formats))}",
                retriable=False
            )

        if file_size > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            file_mb = file_size / (1024 * 1024)
            raise TranscriptionError(
                f"File too large ({file_mb:.1f}MB). Maximum size: {max_mb:.1f}MB",
                retriable=False
            )

    def _log_transcription_start(self, filename: str, file_size: int) -> None:
        """Log transcription attempt for observability."""
        logger.info(
            f"[{self.name}] Starting transcription: {filename} ({file_size} bytes)"
        )

    def _log_transcription_success(self, filename: str, duration: Optional[float]) -> None:
        """Log successful transcription."""
        duration_str = f"{duration:.1f}s" if duration else "unknown"
        logger.info(
            f"[{self.name}] Transcription complete: {filename} (duration: {duration_str})"
        )

    def _log_transcription_error(self, filename: str, error: Exception) -> None:
        """Log transcription failure."""
        logger.error(
            f"[{self.name}] Transcription failed: {filename} - {error}"
        )
