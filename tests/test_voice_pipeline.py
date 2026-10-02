import asyncio

import pytest

from app.audio_output.interruption_handler import InterruptionHandler
from app.conversation.conversation_manager import ConversationManager
from app.pipeline.voice_pipeline import VoicePipeline
from app.utils.latency_logger import TurnTimer


class FakeLLM:
    async def stream(self, messages):
        for tok in ["Hello there, ", "how are you today? ", "I am fine."]:
            yield tok


class FakeTTS:
    async def synthesize_stream(self, sentences):
        async for s in sentences:
            yield s, b"\x00\x00" * 100


class FakePlayer:
    def __init__(self):
        self.sentences = []

    def reset(self):
        self.sentences = []

    def play_sentence(self, text, pcm):
        self.sentences.append(text)

    async def wait_until_done(self):
        pass

    def spoken_text(self):
        return " ".join(self.sentences)

    def stop(self):
        pass


def test_conversation_merges_consecutive_user_turns():
    c = ConversationManager()
    c.add_user("hi")
    c.add_user("are you there")
    assert c.get_messages() == [{"role": "user", "content": "hi are you there"}]


def test_conversation_trims_and_starts_with_user():
    c = ConversationManager(max_messages=3)
    for i in range(4):
        c.add_user(f"u{i}")
        c.add_assistant(f"a{i}")
    msgs = c.get_messages()
    assert msgs[0]["role"] == "user"
    assert len(msgs) <= 3


def test_interrupt_cancels_task_and_stops_player():
    stopped = []

    class P:
        def stop(self):
            stopped.append(True)

    async def scenario():
        handler = InterruptionHandler(P())
        task = asyncio.create_task(asyncio.sleep(10))
        handler.attach(task)
        assert handler.interrupt() is True
        with pytest.raises(asyncio.CancelledError):
            await task
        assert handler.interrupt() is False

    asyncio.run(scenario())
    assert stopped


def test_respond_saves_spoken_text_in_history():
    p = VoicePipeline(mic=object(), detector=object(), stt=object(),
                      llm=FakeLLM(), tts=FakeTTS(), player=FakePlayer())
    p.conv.add_user("hi")
    asyncio.run(p.respond(TurnTimer()))
    last = p.conv.get_messages()[-1]
    assert last["role"] == "assistant"
    assert "how are you today?" in last["content"]