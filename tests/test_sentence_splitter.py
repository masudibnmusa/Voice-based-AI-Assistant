import asyncio

from app.tts.sentence_splitter import split_sentences


async def _agen(tokens):
    for t in tokens:
        yield t


def collect(tokens, **kw):
    async def run():
        return [s async for s in split_sentences(_agen(tokens), **kw)]
    return asyncio.run(run())


def test_splits_on_sentence_end():
    out = collect(["Hello there, ", "how are you? ", "I am fine. ", "Thanks!"])
    assert out == ["Hello there, how are you?", "I am fine. Thanks!"]


def test_min_chars_one_splits_every_sentence():
    out = collect(["Hello there, ", "how are you? ", "I am fine. ", "Thanks!"], min_chars=1)
    assert out == ["Hello there, how are you?", "I am fine.", "Thanks!"]


def test_does_not_split_decimals():
    out = collect(["The value is 3.5 percent today. ", "Next."], min_chars=5)
    assert out == ["The value is 3.5 percent today.", "Next."]


def test_flushes_remainder_without_punctuation():
    assert collect(["no punctuation here"]) == ["no punctuation here"]