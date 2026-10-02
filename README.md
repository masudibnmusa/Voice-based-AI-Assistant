# Voice Assistant

A voice-driven conversational agent. You speak, your audio is transcribed, an LLM generates a reply, and the reply is spoken back to you, with every stage streaming so the conversation feels natural.

```
Mic → VAD → Speech-to-Text → LLM (streaming) → Sentence Splitter → Text-to-Speech → Speaker
        ↑                                                                              |
        └──────────────── Barge-in: user interrupts, playback + LLM cancelled ─────────┘
```

The hard part of this project isn't the LLM. It's making the full pipeline feel natural: low latency, clean interruption handling, streaming audio instead of waiting for full responses, and knowing when the user has finished speaking.

## Features

- Push-to-talk or continuous listening with voice activity detection (VAD)
- Streaming speech-to-text (Whisper API, Deepgram, or AssemblyAI)
- Streaming LLM responses (Claude by default; GPT also supported)
- Sentence-chunked text-to-speech (ElevenLabs, OpenAI TTS, or PlayHT)
- Barge-in: interrupt the assistant mid-sentence and it stops immediately
- Multi-turn conversation history
- Per-stage latency logging
- Optional wake word ("Hey Assistant") via Porcupine

## How it works

1. **Audio capture**: microphone input via `sounddevice`
2. **VAD**: detects when you start and stop speaking (Silero VAD or WebRTC VAD)
3. **STT**: transcribes the utterance to text
4. **LLM**: receives the transcript plus conversation history and streams tokens back
5. **Sentence splitter**: groups the token stream into speakable chunks
6. **TTS**: converts each chunk to audio as soon as it is ready
7. **Playback**: streams audio to the speaker while later sentences are still generating
8. **Interruption handler**: if you speak during playback, it stops audio and cancels the LLM and TTS tasks

## Project structure

```
voice-assistant/
├── app/
│   ├── main.py                        # Entry point (local app / WebSocket server)
│   ├── config.py                      # API keys, voice settings, latency thresholds
│   ├── audio_input/
│   │   ├── mic_capture.py             # Raw microphone capture
│   │   ├── vad.py                     # Voice activity detection
│   │   └── wake_word_detector.py      # Optional wake word detection
│   ├── stt/
│   │   ├── transcriber.py             # Whisper/Deepgram/AssemblyAI wrapper
│   │   └── streaming_transcriber.py   # Streaming STT for lower latency
│   ├── conversation/
│   │   ├── conversation_manager.py    # Turn history and context window
│   │   ├── llm_client.py              # Streaming LLM wrapper
│   │   └── prompt_templates.py        # System prompt tuned for spoken replies
│   ├── tts/
│   │   ├── synthesizer.py             # ElevenLabs/OpenAI TTS/PlayHT wrapper
│   │   ├── streaming_synthesizer.py   # Sentence-chunked streaming TTS
│   │   └── sentence_splitter.py       # Splits LLM stream into speakable chunks
│   ├── audio_output/
│   │   ├── player.py                  # Streams audio chunks to the speaker
│   │   └── interruption_handler.py    # Barge-in: stop playback, cancel LLM call
│   ├── pipeline/
│   │   └── voice_pipeline.py          # Orchestrates listen → transcribe → respond → speak
│   └── utils/
│       ├── audio_utils.py             # Format conversion, resampling
│       └── latency_logger.py          # Time spent in each pipeline stage
├── data/
│   ├── conversation_logs/             # Saved transcripts + audio (optional)
│   └── voice_profiles/                # Custom voice settings per user/persona
├── tests/
│   ├── test_vad.py
│   ├── test_transcriber.py
│   ├── test_sentence_splitter.py
│   └── test_voice_pipeline.py
├── .env.example
├── requirements.txt
├── README.md
└── run.sh
```

## Data flow

```
Mic audio → vad.py                      (detect speech start/end)
          → streaming_transcriber.py    (audio → text)
          → conversation_manager.py     (add to history, build prompt)
          → llm_client.py               (stream response token by token)
          → sentence_splitter.py        (chunk into speakable units)
          → streaming_synthesizer.py    (text chunk → audio chunk)
          → player.py                   (play audio as it arrives)

If the user speaks during playback:
          → interruption_handler.py     (stop playback, cancel LLM stream)
          → loop back to vad.py
```

## Getting started

### Prerequisites

- Python 3.10+
- A working microphone and speakers (use headphones while developing; see [Known issues](#known-issues))
- API keys for your chosen STT, LLM, and TTS providers

### Installation

```bash
git clone https://github.com/masudibnmusa/Voice-based-AI-Assistant.git
cd voice-assistant

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

### Configuration

Edit `.env` with your keys:

```env
ANTHROPIC_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
# or OPENAI_API_KEY for Whisper / OpenAI TTS
```

Tunable settings live in `app/config.py`:

| Setting | Description | Typical value |
|---|---|---|
| `LLM_MODEL` | Model used for replies | `claude-sonnet-5-5` |
| `VAD_THRESHOLD` | Speech probability needed to count as speech | `0.5` |
| `END_OF_TURN_SILENCE_MS` | Silence before the turn is considered finished | `500-800` |
| `MAX_REPLY_TOKENS` | Cap on reply length | `300` |
| `TTS_VOICE` | Voice ID / name | provider-specific |
| `SAMPLE_RATE` | Input sample rate for VAD/STT | `16000` |

### Run

```bash
./run.sh
# or
python -m app.main
```

## Suggested build order

Build in layers. Get a slow-but-working version first, then make it fast.

1. **Push-to-talk, no streaming.** Record while a key is held, transcribe, call the LLM normally, synthesize the full reply, play it. Expect 4-5 seconds of latency; that's fine.
2. **Replace push-to-talk with VAD.** Run Silero VAD on ~30 ms frames. Start recording when speech probability stays above the threshold, stop after 500-800 ms of silence.
3. **Stream the LLM into sentence-chunked TTS.** The biggest latency win: speak sentence one while the rest is still generating.
4. **Barge-in.** Keep VAD running during playback. On speech, stop the player and cancel the LLM and TTS tasks.
5. **Optimizations.** Streaming STT, latency logging, wake word detection.

## Design notes

### Prompt for speech

Replies are spoken, not read. The system prompt in `prompt_templates.py` should enforce:

- 1-3 short sentences unless asked for more
- No markdown, bullet points, emojis, or URLs
- Numbers and symbols written the way they would be said
- A conversational tone

### Pipelining

Run synthesis and playback as two separate async tasks connected by an `asyncio.Queue`, so sentence 2 is being synthesized while sentence 1 is playing.

### Barge-in

The pipeline runs the response as a cancellable `asyncio` task. When VAD detects speech during playback, the task is cancelled, the player is stopped, and the loop returns to listening. On interruption, store only the text that was actually spoken in the conversation history, not the full generated reply.

## Latency

Target: **under ~1 second** from end of speech to first audio.

`latency_logger.py` records time spent in each stage (VAD end-of-turn, STT, LLM time-to-first-token, TTS time-to-first-byte, playback start). Enable it from the start so you know where the time goes.

## Known issues

- **Echo:** the mic picks up the assistant's own voice and can trigger false barge-ins. Use headphones during development; add acoustic echo cancellation (e.g., WebRTC AEC) later.
- **Sample rates:** VAD typically needs 16 kHz mono while TTS often outputs 24 kHz. Use `audio_utils.py` for resampling.
- **End-of-turn tuning:** too short a silence window cuts people off; too long feels sluggish.

## Testing

```bash
pytest tests/
```

## Suggested stack

| Stage | Options |
|---|---|
| VAD | Silero VAD, WebRTC VAD |
| STT | Deepgram (streaming), AssemblyAI, Whisper API |
| LLM | Claude (streaming), GPT |
| TTS | ElevenLabs, OpenAI TTS, PlayHT |
| Audio I/O | `sounddevice` |
| Wake word | Porcupine |

## License

MIT