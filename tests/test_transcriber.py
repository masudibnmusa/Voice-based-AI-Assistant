import asyncio
import io
import wave
from types import SimpleNamespace

import numpy as np

from app.stt.transcriber import Transcriber
from app.utils.audio_utils import pcm16_to_wav_bytes


def test_wav_conversion_is_valid():
    audio = (np.random.randn(16000) * 1000).astype(np.int16)
    wav = pcm16_to_wav_bytes(audio, 16000)
    with wave.open(io.BytesIO(wav)) as w:
        assert w.getframerate() == 16000
        assert w.getnchannels() == 1
        assert w.getnframes() == 16000


def test_transcriber_returns_stripped_text():
    class FakeTranscriptions:
        async def create(self, **kwargs):
            return SimpleNamespace(text="  hello world  ")

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=FakeTranscriptions()))
    audio = np.zeros(16000, dtype=np.int16)
    assert asyncio.run(Transcriber(client=client).transcribe(audio)) == "hello world"