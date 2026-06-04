import io
import threading
from typing import Optional

import numpy as np
import soundfile as sf

from app.tts.base import EngineInfo, MAX_TEXT_LENGTH

SAMPLE_RATE = 24000

VOICES = [
    "af_heart",
    "af_bella",
    "af_nicole",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_michael",
    "bf_emma",
    "bf_isabella",
    "bm_george",
    "bm_lewis",
]

DEFAULT_VOICE = "af_heart"


class KokoroEngine:
    name = "kokoro"
    label = "Kokoro"

    def __init__(self) -> None:
        self._pipeline = None
        self._lock = threading.Lock()
        self._loading = False
        self._load_error: Optional[str] = None

    def load(self) -> None:
        if self._pipeline is not None:
            return

        with self._lock:
            if self._pipeline is not None:
                return

            self._loading = True
            self._load_error = None
            try:
                from kokoro import KPipeline

                self._pipeline = KPipeline(lang_code="a")
            except Exception as exc:
                self._load_error = str(exc)
                raise
            finally:
                self._loading = False

    def is_loaded(self) -> bool:
        return self._pipeline is not None

    def is_loading(self) -> bool:
        return self._loading

    def get_load_error(self) -> Optional[str]:
        return self._load_error

    def get_info(self) -> EngineInfo:
        return EngineInfo(
            name=self.name,
            label=self.label,
            model_loaded=self.is_loaded(),
            loading=self.is_loading(),
            load_error=self._load_error,
            device="cpu",
            voices=VOICES,
        )

    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        trimmed = text.strip()
        if not trimmed:
            raise ValueError("Text cannot be empty")
        if len(trimmed) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text exceeds {MAX_TEXT_LENGTH} character limit")

        self.load()
        if self._pipeline is None:
            raise RuntimeError(self._load_error or "Kokoro failed to load")

        selected_voice = voice or DEFAULT_VOICE
        if selected_voice not in VOICES:
            raise ValueError(f"Unknown voice: {selected_voice}")

        chunks = [
            audio for _, _, audio in self._pipeline(trimmed, voice=selected_voice)
        ]
        if not chunks:
            raise RuntimeError("Kokoro produced no audio")

        audio = np.concatenate(chunks)
        buffer = io.BytesIO()
        sf.write(buffer, audio, SAMPLE_RATE, format="WAV")
        buffer.seek(0)
        return buffer.read()


engine = KokoroEngine()


def preload() -> None:
    try:
        engine.load()
    except Exception:
        pass
