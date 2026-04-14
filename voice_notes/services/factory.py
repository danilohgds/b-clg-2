"""
Factory for creating transcription service instances.

Supports configuration via Django settings to switch providers without code changes.
"""
from django.conf import settings
from .base import TranscriptionService, TranscriptionError


def get_transcription_service() -> TranscriptionService:
    """
    Factory function to get the configured transcription service.

    Configuration via settings.VOICE_NOTE_TRANSCRIPTION_PROVIDER:
    - 'openai': OpenAI Whisper API (default)
    - 'local': Local Whisper model via faster-whisper
    - 'mock': Mock service for testing

    Returns:
        Configured TranscriptionService instance

    Raises:
        TranscriptionError: If provider is unknown or misconfigured
    """
    provider = getattr(settings, 'VOICE_NOTE_TRANSCRIPTION_PROVIDER', 'openai')

    if provider == 'openai':
        from .openai_whisper import OpenAIWhisperService
        return OpenAIWhisperService()

    elif provider == 'local':
        from .local_whisper import LocalWhisperService
        return LocalWhisperService()

    elif provider == 'mock':
        from .mock import MockTranscriptionService
        # Allow configuring mock transcript via settings
        mock_transcript = getattr(
            settings,
            'VOICE_NOTE_MOCK_TRANSCRIPT',
            'Mock transcript for testing.'
        )
        return MockTranscriptionService(transcript=mock_transcript)

    else:
        raise TranscriptionError(
            f"Unknown transcription provider: '{provider}'. "
            f"Valid options: 'openai', 'local', 'mock'",
            retriable=False
        )
