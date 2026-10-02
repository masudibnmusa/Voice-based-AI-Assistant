import asyncio

import sounddevice as sd

from app import config


class MicCapture:
    """Captures mono int16 audio in fixed-size frames and exposes them as an async iterator."""

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._loop = None
        self._stream = None

    def _callback(self, indata, frames, time_info, status):
        # Runs in PortAudio's thread, so hand the frame to the event loop safely.
        self._loop.call_soon_threadsafe(self._queue.put_nowait, indata[:, 0].copy())

    def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._stream = sd.InputStream(
            samplerate=config.INPUT_SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=config.FRAME_SAMPLES,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    async def frames(self):
        while True:
            yield await self._queue.get()