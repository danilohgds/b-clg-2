from django.contrib import admin
from .models import VoiceNote


@admin.register(VoiceNote)
class VoiceNoteAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'booking',
        'status',
        'audio_duration_seconds',
        'created_at',
        'created_by'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['booking__id', 'transcript', 'created_by']
    readonly_fields = ['created_at', 'updated_at', 'transcribed_at']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('booking', 'status', 'created_by')
        }),
        ('Audio', {
            'fields': ('audio_file', 'audio_duration_seconds', 'audio_file_size')
        }),
        ('Transcription', {
            'fields': ('transcript', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'transcribed_at'),
            'classes': ('collapse',)
        }),
    )
