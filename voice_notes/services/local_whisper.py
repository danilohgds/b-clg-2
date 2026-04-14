"""
Local Whisper implementation for transcription.

Uses faster-whisper (CTranslate2 optimized) for efficient local transcription.
No API calls - runs entirely on your machine.

Install: pip install faster-whisper
"""
import logging
import tempfile
import os
from typing import BinaryIO, Set, Optional
from django.conf import settings
from .base import TranscriptionService, TranscriptionResult, TranscriptionError

logger = logging.getLogger(__name__)

# Lazy load to avoid import errors when not installed
_whisper_model = None


def _get_whisper_model():
    """Lazily load the Whisper model."""
    global _whisper_model

    if _whisper_model is not None:
        return _whisper_model

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscriptionError(
            "faster-whisper not installed. Run: pip install faster-whisper",
            retriable=False
        )

    model_size = getattr(settings, 'WHISPER_MODEL_SIZE', 'base')
    device = getattr(settings, 'WHISPER_DEVICE', 'auto')  # 'auto', 'cpu', 'cuda'
    compute_type = getattr(settings, 'WHISPER_COMPUTE_TYPE', 'auto')  # 'auto', 'int8', 'float16'

    logger.info(f"Loading Whisper model: {model_size} (device={device}, compute={compute_type})")

    try:
        # For CPU, use int8 for speed. For GPU, use float16.
        if device == 'auto':
            # Try CUDA first, fall back to CPU
            try:
                _whisper_model = WhisperModel(model_size, device='cuda', compute_type='float16')
                logger.info("Using CUDA (GPU) for Whisper")
            except Exception:
                _whisper_model = WhisperModel(model_size, device='cpu', compute_type='int8')
                logger.info("Using CPU for Whisper")
        else:
            actual_compute = compute_type if compute_type != 'auto' else ('float16' if device == 'cuda' else 'int8')
            _whisper_model = WhisperModel(model_size, device=device, compute_type=actual_compute)

        return _whisper_model

    except Exception as e:
        raise TranscriptionError(
            f"Failed to load Whisper model '{model_size}': {e}",
            retriable=False
        )


class LocalWhisperService(TranscriptionService):
    """
    Local Whisper transcription using faster-whisper.

    Features:
    - Runs entirely locally (no API calls)
    - Free (no per-minute costs)
    - Privacy-preserving (audio never leaves your machine)
    - GPU acceleration if available

    Configuration:
    - WHISPER_MODEL_SIZE: Model size (tiny/base/small/medium/large)
      - tiny: ~75MB, fastest, lowest accuracy
      - base: ~140MB, good balance (default)
      - small: ~460MB, better accuracy
      - medium: ~1.5GB, high accuracy
      - large: ~3GB, best accuracy
    - WHISPER_DEVICE: 'auto', 'cpu', or 'cuda'
    - WHISPER_COMPUTE_TYPE: 'auto', 'int8', 'float16', 'float32'
    """

    @property
    def name(self) -> str:
        model_size = getattr(settings, 'WHISPER_MODEL_SIZE', 'base')
        return f"Local Whisper ({model_size})"

    @property
    def supported_formats(self) -> Set[str]:
        # Whisper supports most audio formats via ffmpeg
        return {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm', '.ogg', '.flac'}

    @property
    def max_file_size_bytes(self) -> int:
        # Local processing can handle larger files
        return 100 * 1024 * 1024  # 100MB

    def transcribe(self, audio_file: BinaryIO, filename: str) -> TranscriptionResult:
        """
        Transcribe audio using local Whisper model.

        Args:
            audio_file: File-like object with audio data
            filename: Original filename for format detection

        Returns:
            TranscriptionResult with transcript text

        Raises:
            TranscriptionError: On processing failures
        """
        # Get file size for logging
        audio_file.seek(0, 2)
        file_size = audio_file.tell()
        audio_file.seek(0)

        self._log_transcription_start(filename, file_size)

        # Save to temp file (faster-whisper needs a file path)
        ext = os.path.splitext(filename)[1].lower() or '.ogg'
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(audio_file.read())
                tmp_path = tmp.name

            try:
                model = _get_whisper_model()

                # Transcribe
                segments, info = model.transcribe(
                    tmp_path,
                    beam_size=5,
                    language=None,  # Auto-detect
                    vad_filter=True,  # Filter out silence
                )

                # Combine segments into full text
                text_parts = []
                for segment in segments:
                    text_parts.append(segment.text.strip())

                full_text = ' '.join(text_parts).strip()

                result = TranscriptionResult(
                    text=full_text,
                    duration_seconds=info.duration,
                    language=info.language,
                    confidence=info.language_probability
                )

                self._log_transcription_success(filename, result.duration_seconds)
                return result

            finally:
                # Clean up temp file
                os.unlink(tmp_path)

        except TranscriptionError:
            raise
        except Exception as e:
            self._log_transcription_error(filename, e)
            raise TranscriptionError(
                f"Local transcription failed: {e}",
                retriable=True
            )
