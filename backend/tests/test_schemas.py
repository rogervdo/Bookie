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


def test_synthesize_request_rejects_text_over_limit():
    with pytest.raises(ValidationError):
        SynthesizeRequest(text="x" * 9001)


def test_synthesize_request_accepts_text_at_limit():
    req = SynthesizeRequest(text="x" * 9000)
    assert len(req.text) == 9000


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
