"""
Utility functions for voice notes.
"""
import logging
import subprocess
import tempfile
import os
from typing import BinaryIO, Optional

logger = logging.getLogger(__name__)


def get_audio_duration(audio_file: BinaryIO) -> Optional[float]:
    """
    Get the duration of an audio file in seconds.

    Uses ffprobe if available, otherwise returns None.

    Args:
        audio_file: File-like object containing audio data

    Returns:
        Duration in seconds, or None if unable to determine
    """
    try:
        # Save to temp file for ffprobe
        with tempfile.NamedTemporaryFile(delete=False, suffix='.audio') as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        try:
            result = subprocess.run(
                [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    tmp_path
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())

        finally:
            os.unlink(tmp_path)

    except FileNotFoundError:
        logger.debug("ffprobe not found, cannot determine audio duration")
    except subprocess.TimeoutExpired:
        logger.warning("ffprobe timed out")
    except Exception as e:
        logger.warning(f"Error getting audio duration: {e}")

    return None


def get_audio_duration_mutagen(audio_file: BinaryIO, filename: str) -> Optional[float]:
    """
    Alternative duration detection using mutagen library.

    Falls back to this if ffprobe is not available.

    Args:
        audio_file: File-like object
        filename: Original filename (for format detection)

    Returns:
        Duration in seconds, or None if unable to determine
    """
    try:
        from mutagen import File as MutagenFile

        # Save to temp file
        ext = os.path.splitext(filename)[1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name

        try:
            audio = MutagenFile(tmp_path)
            if audio and audio.info:
                return audio.info.length
        finally:
            os.unlink(tmp_path)

    except ImportError:
        logger.debug("mutagen not installed")
    except Exception as e:
        logger.warning(f"Error getting audio duration with mutagen: {e}")

    return None
