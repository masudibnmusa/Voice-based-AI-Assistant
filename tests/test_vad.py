import numpy as np

from app import config
from app.audio_input.vad import SPEECH_END, SPEECH_START, TurnDetector


class FakeVAD:
    def prob(self, frame):
        return 1.0 if frame[0] else 0.0

    def reset(self):
        pass


SPEECH = np.ones(config.FRAME_SAMPLES, dtype=np.int16)
SILENCE = np.zeros(config.FRAME_SAMPLES, dtype=np.int16)


def run(frames):
    det = TurnDetector(vad=FakeVAD())
    events = []
    for f in frames:
        event, audio = det.process(f)
        if event:
            events.append((event, audio))
    return events


def test_full_utterance_emits_start_and_end():
    frames = [SPEECH] * 20 + [SILENCE] * (config.END_FRAMES + 1)
    events = run(frames)
    assert [e for e, _ in events] == [SPEECH_START, SPEECH_END]
    assert len(events[1][1]) >= 20 * config.FRAME_SAMPLES


def test_short_blip_is_ignored():
    assert run([SPEECH] + [SILENCE] * 50) == []


def test_silence_only_emits_nothing():
    assert run([SILENCE] * 100) == []