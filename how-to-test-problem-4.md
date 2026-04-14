#HOW TO TEST

Problem 4 was done using the OPENAI Whisper API, this means we should use an OPENAI API KEY for it, the VOICE_NOTE_PROVIDER env variable being set to openai.

Alternatively, if you set it to "local" this will run whisper locally and speed/performance will be relying on the computer's GPU/CPU. Whisper model is about 1GB locally, while providing the same accuracy of the whisper api.

