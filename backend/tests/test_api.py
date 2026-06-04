import pytest
from fastapi.testclient import TestClient

from app.tts.kokoro import DEFAULT_VOICE, VOICES, KokoroEngine


def test_health_returns_kokoro_status(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert "af_heart" in data["voices"]


def test_health_shows_loading(client: TestClient, mock_engine):
    mock_engine._model_loaded = False
    mock_engine._loading = True

    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "loading"


def test_synthesize_returns_wav(client: TestClient, mock_engine):
    response = client.post(
        "/api/synthesize",
        json={"text": "Hello world", "voice": "af_heart"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == b"RIFFmock"
    assert mock_engine.last_synthesize == ("Hello world", "af_heart")


def test_synthesize_rejects_empty_text(client: TestClient):
    response = client.post("/api/synthesize", json={"text": ""})
    assert response.status_code == 422


def test_synthesize_rejects_text_over_limit(client: TestClient):
    response = client.post("/api/synthesize", json={"text": "x" * 501})
    assert response.status_code == 422


def test_synthesize_returns_503_while_loading(client: TestClient, mock_engine):
    mock_engine._model_loaded = False
    mock_engine._loading = True

    response = client.post("/api/synthesize", json={"text": "Hello"})
    assert response.status_code == 503
    assert "loading" in response.json()["detail"].lower()


def test_synthesize_returns_503_on_load_error(client: TestClient, mock_engine):
    mock_engine._model_loaded = False
    mock_engine._loading = False
    mock_engine._load_error = "Model download failed"

    response = client.post("/api/synthesize", json={"text": "Hello"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Model download failed"


def test_synthesize_returns_400_for_validation_error(
    client: TestClient, mock_engine
):
    mock_engine._synthesize_error = ValueError("Unknown voice: bad_voice")

    response = client.post(
        "/api/synthesize",
        json={"text": "Hello", "voice": "bad_voice"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown voice: bad_voice"


def test_kokoro_default_voice_in_catalog():
    assert DEFAULT_VOICE in VOICES


def test_kokoro_rejects_empty_text(fake_pipeline):
    engine = KokoroEngine()
    engine._pipeline = fake_pipeline

    with pytest.raises(ValueError, match="empty"):
        engine.synthesize("   ")


def test_kokoro_rejects_unknown_voice(fake_pipeline):
    engine = KokoroEngine()
    engine._pipeline = fake_pipeline

    with pytest.raises(ValueError, match="Unknown voice"):
        engine.synthesize("Hello", voice="not_real")


def test_kokoro_synthesizes_with_mock_pipeline(fake_pipeline):
    engine = KokoroEngine()
    engine._pipeline = fake_pipeline

    wav = engine.synthesize("Hello there", voice="af_heart")
    assert wav.startswith(b"RIFF")
