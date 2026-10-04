"""Speech-to-text via any OpenAI-compatible Whisper endpoint (OpenAI, Groq, local)."""
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ALLOWED_EXT = {".webm", ".ogg", ".oga", ".m4a", ".mp3", ".mp4", ".mpeg", ".mpga", ".wav"}
MIME = {".webm": "audio/webm", ".ogg": "audio/ogg", ".oga": "audio/ogg", ".m4a": "audio/mp4",
        ".mp4": "audio/mp4", ".mp3": "audio/mpeg", ".mpeg": "audio/mpeg", ".mpga": "audio/mpeg",
        ".wav": "audio/wav"}

# Vocabulary hint: Whisper biases toward these spellings/words.
PROMPT_HINT = ("Dukaan ka hisaab: chawal, atta, cheeni, daal, ghee, doodh, tel, packet, kilo, "
               "udhaar, khatam, bik gaye, aa gaya, de gaya. چاول، آٹا، چینی، دال، گھی، ادھار، ختم، پیکٹ، کلو")


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(base_url=os.getenv("STT_BASE_URL") or None,
                  api_key=os.getenv("STT_API_KEY", "missing-key"),
                  timeout=float(os.getenv("STT_TIMEOUT", "60")))


def transcribe(audio_bytes: bytes, filename: str) -> str:
    if not audio_bytes:
        raise ValueError("Empty audio")
    ext = Path((filename or "").split(";")[0]).suffix.lower() or ".webm"  # "blob" from browsers -> webm
    if ext not in ALLOWED_EXT:
        raise ValueError(f"Unsupported audio format '{ext}'. Use webm/ogg/m4a/mp3/wav.")
    # Browsers often send "blob" or "recording.webm;codecs=opus" — give Whisper a clean name.
    clean_name = f"audio{'.ogg' if ext == '.oga' else ext}"
    resp = _client().audio.transcriptions.create(
        model=os.getenv("STT_MODEL", "whisper-1"),
        file=(clean_name, audio_bytes, MIME[ext]),
        language="ur",
        prompt=PROMPT_HINT,
        temperature=0,
    )
    return (getattr(resp, "text", None) or str(resp)).strip()
