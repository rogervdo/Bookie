from typing import Optional

from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    voice: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    loading: bool
    load_error: Optional[str] = None
    device: Optional[str] = None
    voices: list[str] = []
