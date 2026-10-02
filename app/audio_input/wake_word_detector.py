import numpy as np

from app import config


class WakeWordDetector:
    """Optional. Requires `pip install pvporcupine` and a free Picovoice access key."""

    def __init__(self):
        import pvporcupine

        kwargs = {"access_key": config.PORCUPINE_ACCESS_KEY}
        if config.WAKE_WORD_PATH:
            kwargs["keyword_paths"] = [config.WAKE_WORD_PATH]   # custom "Hey Assistant" .ppn
        else:
            kwargs["keywords"] = [config.WAKE_WORD_BUILTIN]
        self._porcupine = pvporcupine.create(**kwargs)
        assert self._porcupine.frame_length == config.FRAME_SAMPLES
        assert self._porcupine.sample_rate == config.INPUT_SAMPLE_RATE

    def detect(self, frame: np.ndarray) -> bool:
        return self._porcupine.process(frame.tolist()) >= 0

    def close(self) -> None:
        self._porcupine.delete()