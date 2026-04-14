# Test Files for Voice Notes

## test_voice_note.mp3

This is a placeholder file. Replace it with a real MP3 audio file containing the phrase:

> "I am testing a voicenote"

### How to create a test file:

1. Use your phone/laptop to record yourself saying "I am testing a voicenote"
2. Save as MP3 format
3. Replace `test_voice_note.mp3` with your recording

### Testing with the API:

```bash
# Upload to a booking (replace {booking_id} with actual ID)
curl -X POST http://localhost:8006/bookings/{booking_id}/voice-notes/ \
  -F "audio_file=@test_voice_note.mp3"

# List voice notes for booking
curl http://localhost:8006/bookings/{booking_id}/voice-notes/
```

### Expected Result:

When using OpenAI Whisper, the transcript should contain:
> "I am testing a voicenote"

When using mock provider (for testing), the transcript will be:
> "This is a mock transcript for testing purposes."
