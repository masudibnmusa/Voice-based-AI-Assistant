import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "data" / "conversation_logs"
PROFILE_DIR = ROOT / "data" / "voice_profiles"


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# ---- API keys -------------------------------------------------------------
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
PORCUPINE_ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY")

# ---- Audio ----------------------------------------------------------------
INPUT_SAMPLE_RATE = 16000           # Silero VAD + Whisper want 16 kHz mono
OUTPUT_SAMPLE_RATE = 24000          # OpenAI TTS "pcm" output is 24 kHz 16-bit mono
FRAME_SAMPLES = 512                 # Silero needs exactly 512 samples @ 16 kHz
FRAME_MS = FRAME_SAMPLES * 1000 // INPUT_SAMPLE_RATE   # = 32 ms

# ---- VAD / turn detection (latency thresholds) -----------------------------
VAD_THRESHOLD = 0.5                 # speech probability needed to count as speech
END_OF_TURN_SILENCE_MS = 700        # silence that ends a turn (500-800 is typical)
SPEECH_START_FRAMES = 3             # consecutive speech frames to confirm speech start
PRE_ROLL_MS = 300                   # audio kept from before speech was confirmed
MIN_UTTERANCE_MS = 300              # ignore blips shorter than this

END_FRAMES = END_OF_TURN_SILENCE_MS // FRAME_MS
PRE_ROLL_FRAMES = PRE_ROLL_MS // FRAME_MS

# ---- STT ------------------------------------------------------------------
STT_MODEL = "whisper-1"
STT_LANGUAGE = "en"                 # set to None to auto-detect

# ---- LLM ------------------------------------------------------------------
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
MAX_REPLY_TOKENS = 300
MAX_HISTORY_MESSAGES = 20

# ---- TTS ------------------------------------------------------------------
TTS_MODEL = "gpt-4o-mini-tts"
SENTENCE_MIN_CHARS = 20


def load_voice_profile(name: str = "default") -> dict:
    path = PROFILE_DIR / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else {}


VOICE_PROFILE = load_voice_profile(os.getenv("VOICE_PROFILE", "default"))
TTS_VOICE = VOICE_PROFILE.get("voice", "alloy")
TTS_INSTRUCTIONS = VOICE_PROFILE.get("instructions")

# ---- Wake word (optional) -------------------------------------------------
USE_WAKE_WORD = _env_bool("USE_WAKE_WORD", False)
WAKE_WORD_BUILTIN = "computer"      # built-in Porcupine keyword
WAKE_WORD_PATH = None               # path to a custom "Hey Assistant" .ppn file
WAKE_WINDOW_S = 30                  # how long to stay awake after the last activity

# ---- Logging --------------------------------------------------------------
SAVE_LOGS = True


def validate() -> None:
    missing = [k for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY") if not os.getenv(k)]
    if missing:
        raise SystemExit(f"Missing keys in .env: {', '.join(missing)}")