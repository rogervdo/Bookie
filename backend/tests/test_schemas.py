import pytest
from pydantic import ValidationError

from app.schemas import HealthResponse, SynthesizeRequest


def test_synthesize_request_defaults():
    req = SynthesizeRequest(text="Hello")
    assert req.voice is None


def test_synthesize_request_accepts_voice():
    req = SynthesizeRequest(text="Hi", voice="af_heart")
    assert req.voice == "af_heart"


def test_synthesize_request_rejects_empty_text():
    with pytest.raises(ValidationError):
        SynthesizeRequest(text="")


def test_synthesize_request_rejects_text_over_500_chars():
    with pytest.raises(ValidationError):
        SynthesizeRequest(text="x" * 501)


def test_synthesize_request_accepts_500_chars():
    req = SynthesizeRequest(text="x" * 500)
    assert len(req.text) == 500


def test_health_response_shape():
    response = HealthResponse(
        status="ok",
        model_loaded=True,
        loading=False,
        device="cpu",
        voices=["af_heart"],
    )
    assert response.status == "ok"
    assert response.model_loaded is True
