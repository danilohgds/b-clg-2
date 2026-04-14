"""
Serializers for voice notes API.
"""
from rest_framework import serializers
from .models import VoiceNote


class VoiceNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for reading voice note data.

    Used in list and detail responses.
    """
    audio_url = serializers.SerializerMethodField()
    booking_id = serializers.IntegerField(source='booking.id', read_only=True)

    class Meta:
        model = VoiceNote
        fields = [
            'id',
            'booking_id',
            'audio_url',
            'audio_duration_seconds',
            'audio_file_size',
            'transcript',
            'status',
            'error_message',
            'created_at',
            'transcribed_at',
            'created_by',
        ]
        read_only_fields = fields

    def get_audio_url(self, obj) -> str:
        """Get the URL to download the audio file."""
        if obj.audio_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.audio_file.url)
            return obj.audio_file.url
        return None


class VoiceNoteCreateSerializer(serializers.Serializer):
    """
    Serializer for creating voice notes.

    Handles file upload validation.
    """
    audio_file = serializers.FileField(
        help_text="Audio file (mp3, wav, m4a, webm, mp4)"
    )
    created_by = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default='',
        help_text="Identifier of the staff member creating the note"
    )

    def validate_audio_file(self, value):
        """Validate audio file format."""
        allowed_extensions = {'.mp3', '.wav', '.m4a', '.webm', '.mp4', '.ogg'}
        import os
        ext = os.path.splitext(value.name)[1].lower()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported format '{ext}'. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}"
            )

        return value


class VoiceNoteListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for listing voice notes.

    Excludes full transcript for performance.
    """
    transcript_preview = serializers.SerializerMethodField()

    class Meta:
        model = VoiceNote
        fields = [
            'id',
            'audio_duration_seconds',
            'transcript_preview',
            'status',
            'created_at',
        ]

    def get_transcript_preview(self, obj) -> str:
        """Get first 100 chars of transcript."""
        if obj.transcript:
            if len(obj.transcript) > 100:
                return obj.transcript[:100] + "..."
            return obj.transcript
        return ""
