"""
URL patterns for voice notes API.

Voice notes are nested under bookings:
- /bookings/{booking_id}/voice-notes/
- /bookings/{booking_id}/voice-notes/{id}/
- /bookings/{booking_id}/voice-notes/{id}/retry/
"""
from django.urls import path
from .views import VoiceNoteListCreateView, VoiceNoteDetailView, VoiceNoteRetryView

urlpatterns = [
    path('', VoiceNoteListCreateView.as_view(), name='voice-note-list-create'),
    path('<int:pk>/', VoiceNoteDetailView.as_view(), name='voice-note-detail'),
    path('<int:pk>/retry/', VoiceNoteRetryView.as_view(), name='voice-note-retry'),
]
