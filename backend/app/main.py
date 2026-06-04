import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.schemas import HealthResponse, SynthesizeRequest
from app.tts import engine, preload


def create_app(*, preload_on_startup: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if preload_on_startup:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, preload)
        yield

    application = FastAPI(title="Speaking TTS", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        info = engine.get_info()
        return HealthResponse(
            status="loading" if info.loading and not info.model_loaded else "ok",
            model_loaded=info.model_loaded,
            loading=info.loading,
            load_error=info.load_error,
            device=info.device,
            voices=info.voices,
        )

    @application.post("/api/synthesize")
    async def synthesize(request: SynthesizeRequest) -> Response:
        info = engine.get_info()
        if info.loading and not info.model_loaded:
            raise HTTPException(status_code=503, detail="Kokoro is still loading")

        if info.load_error and not info.model_loaded:
            raise HTTPException(status_code=503, detail=info.load_error)

        loop = asyncio.get_event_loop()
        try:
            wav_bytes = await loop.run_in_executor(
                None, engine.synthesize, request.text, request.voice
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        return Response(content=wav_bytes, media_type="audio/wav")

    return application


app = create_app()
