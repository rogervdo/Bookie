import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.tts.kokoro import DEFAULT_VOICE, VOICES, KokoroEngine


class MockEngine:
    def __init__(
        self,
        *,
        model_loaded: bool = True,
        loading: bool = False,
        load_error: str | None = None,
        device: str = "cpu",
        voices: list[str] | None = None,
        wav_bytes: bytes = b"RIFFmock",
        synthesize_error: Exception | None = None,
    ) -> None:
        self.name = "kokoro"
        self.label = "Kokoro"
        self._model_loaded = model_loaded
        self._loading = loading
        self._load_error = load_error
        self._device = device
        self._voices = voices or ["af_heart", "af_bella"]
        self._wav_bytes = wav_bytes
        self._synthesize_error = synthesize_error
        self.last_synthesize: tuple[str, str | None] | None = None

    def load(self) -> None:
        pass

    def is_loaded(self) -> bool:
        return self._model_loaded

    def is_loading(self) -> bool:
        return self._loading

    def get_load_error(self) -> str | None:
        return self._load_error

    def get_info(self):
        from app.tts.base import EngineInfo

        return EngineInfo(
            name=self.name,
            label=self.label,
            model_loaded=self._model_loaded,
            loading=self._loading,
            load_error=self._load_error,
            device=self._device,
            voices=self._voices,
        )

    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        self.last_synthesize = (text, voice)
        if self._synthesize_error:
            raise self._synthesize_error
        return self._wav_bytes


@pytest.fixture
def mock_engine() -> MockEngine:
    return MockEngine()


@pytest.fixture
def client(mock_engine: MockEngine, monkeypatch):
    monkeypatch.setattr("app.main.engine", mock_engine)
    app = create_app(preload_on_startup=False)
    return TestClient(app)


@pytest.fixture
def fake_pipeline():
    class FakePipeline:
        def __call__(self, text: str, voice: str = "af_heart"):
            yield None, None, np.zeros(2400, dtype=np.float32)

    return FakePipeline()
