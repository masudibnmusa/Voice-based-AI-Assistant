import collections

import numpy as np
import torch

from app import config

SPEECH_START = "speech_start"
SPEECH_END = "speech_end"


class SileroVAD:
    """Returns the speech probability of one 512-sample, 16 kHz frame."""

    def __init__(self):
        from silero_vad import load_silero_vad
        self.model = load_silero_vad()

    def prob(self, frame: np.ndarray) -> float:
        x = torch.from_numpy(frame.astype(np.float32) / 32768.0)
        with torch.no_grad():
            return float(self.model(x, config.INPUT_SAMPLE_RATE).item())

    def reset(self) -> None:
        self.model.reset_states()


class TurnDetector:
    """
    Feed it one frame at a time. It returns (event, audio):
      (SPEECH_START, None)   when the user begins talking
      (SPEECH_END, audio)    when they stop, with audio as an int16 numpy array
      (None, None)           otherwise
    """

    def __init__(self, vad=None):
        self.vad = vad or SileroVAD()
        self.pre_roll = collections.deque(maxlen=config.PRE_ROLL_FRAMES)
        self._reset()

    def _reset(self) -> None:
        self.pre_roll.clear()
        self.frames: list = []
        self.in_speech = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.vad.reset()

    def process(self, frame: np.ndarray):
        is_speech = self.vad.prob(frame) >= config.VAD_THRESHOLD

        if not self.in_speech:
            self.pre_roll.append(frame)
            self.speech_frames = self.speech_frames + 1 if is_speech else 0
            if self.speech_frames >= config.SPEECH_START_FRAMES:
                self.in_speech = True
                self.frames = list(self.pre_roll)
                self.silence_frames = 0
                return SPEECH_START, None
            return None, None

        self.frames.append(frame)
        if is_speech:
            self.silence_frames = 0
            return None, None

        self.silence_frames += 1
        if self.silence_frames >= config.END_FRAMES:
            audio = np.concatenate(self.frames)
            self._reset()
            duration_ms = len(audio) * 1000 / config.INPUT_SAMPLE_RATE
            if duration_ms < config.MIN_UTTERANCE_MS:
                return None, None
            return SPEECH_END, audio
        return None, None