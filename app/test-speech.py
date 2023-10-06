import source.audio.speaker as Speaker
import time
import asyncio

Speaker.text_to_speech("One two three")
Speaker.play_wav_bytes("speaker_output.wav")
#await playback_task
