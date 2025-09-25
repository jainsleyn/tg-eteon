
# ---- config ----
import os
import logging

# Optional: load environment from .env if present
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# ---- env & constants ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro").strip()

# Minimalism: default tools all off except search
DEFAULT_SEARCH = True
DEFAULT_URL = False
DEFAULT_CODE = False

# Reasoning budgets (tokens) including dynamic sentinel
THINKING_DYNAMIC = -1
TH_BUDGETS = {"low": 8192, "medium": 16384, "high": 32768, "dynamic": THINKING_DYNAMIC}

# Generation and memory
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "65536"))
MEMORY_TOKEN_LIMIT = int(os.getenv("MEMORY_TOKEN_LIMIT", "1000000"))

# Files API threshold (approx, switch to upload for large requests)
FILES_API_THRESHOLD_BYTES = int(os.getenv("FILES_API_THRESHOLD_BYTES", str(20 * 1024 * 1024)))

# UI / UX
PROGRESS_EDIT_INTERVAL = float(os.getenv("PROGRESS_EDIT_INTERVAL", "2.5"))  # seconds, throttle edits
TYPING_INTERVAL = float(os.getenv("TYPING_INTERVAL", "4.0"))                # seconds
TELEGRAM_CHUNK_SIZE = int(os.getenv("TELEGRAM_CHUNK_SIZE", "3500"))         # safe under hard limit
TELEGRAM_HARD_LIMIT = int(os.getenv("TELEGRAM_HARD_LIMIT", "4096"))

# Streaming
ENABLE_STREAMING = os.getenv("ENABLE_STREAMING", "1").strip() in ("1", "true", "True", "yes")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
log = logging.getLogger("gemini_bot")

def ensure_env() -> None:
    """Fail fast if required env vars are missing."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    if not GEMINI_API_KEY:
        raise SystemExit("GEMINI_API_KEY is not set")
