# Speaking — Handoff Document

**Date:** June 3, 2026  
**Workspace:** `/Users/roger/Speaking`  
**Status:** Demo-ready (Kokoro TTS test tab working)

---

## 1. Project goal

Build a **local, Audible-style text-to-speech app** that runs entirely on-device — no cloud API keys, no usage caps. The long-term vision is a personal audiobook reader (library, chapters, playback controls). **What exists today** is a working **demo/test tab**: paste text, pick a narrator voice, click Read, hear audio in the browser.

---

## 2. Current state (what works)

| Area | Status |
|------|--------|
| Backend API | ✅ FastAPI on port 8000 |
| TTS engine | ✅ Kokoro-82M (Apache 2.0) |
| Frontend UI | ✅ Vite + React + Tailwind demo tab |
| Voice picker | ✅ 11 built-in Kokoro voices |
| Unit tests | ✅ 18 backend (pytest) + 4 frontend (vitest) |
| Git repo | ❌ Not initialized |

**Verified behavior:**
- Kokoro loads on CPU in ~5–10 seconds after first download
- Short sentence synthesis completes in a few seconds
- Health endpoint reports model status and available voices
- Frontend polls `/api/health` until model is ready, then enables Read

---

## 3. Architecture

```
┌─────────────────────────────────────┐
│  Frontend (localhost:5173)          │
│  Vite + React + Tailwind            │
│  - textarea, voice dropdown, Read   │
│  - proxies /api/* → backend         │
└──────────────┬──────────────────────┘
               │ POST /api/synthesize
               │ GET  /api/health
               ▼
┌─────────────────────────────────────┐
│  Backend (localhost:8000)           │
│  FastAPI                            │
│  └── app/tts/kokoro.py              │
│      KPipeline → WAV bytes          │
└─────────────────────────────────────┘
```

### Key files

```
Speaking/
├── HANDOFF.md              ← this document
├── README.md               ← quick setup guide
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI routes, create_app() for tests
│   │   ├── schemas.py      # Pydantic request/response models
│   │   └── tts/
│   │       ├── base.py     # EngineInfo, MAX_TEXT_LENGTH (500)
│   │       └── kokoro.py   # KokoroEngine singleton + preload()
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   └── tests/              # mocked engine — no model download in CI
└── frontend/
    ├── src/
    │   ├── App.tsx         # demo/test tab UI
    │   ├── api.ts          # fetchHealth, synthesize
    │   └── api.test.ts
    └── vite.config.ts      # /api proxy → :8000
```

---

## 4. API reference

### `GET /api/health`

```json
{
  "status": "ok",
  "model_loaded": true,
  "loading": false,
  "load_error": null,
  "device": "cpu",
  "voices": ["af_heart", "af_bella", "..."]
}
```

### `POST /api/synthesize`

**Request:**
```json
{ "text": "Hello world", "voice": "af_heart" }
```

**Response:** `audio/wav` (24 kHz mono PCM)

**Limits:** 1–500 characters per request (demo cap)

**Errors:**
| Code | When |
|------|------|
| 422 | Empty or too-long text |
| 503 | Model still loading or failed to load |
| 400 | Unknown voice, validation error |
| 500 | Unexpected synthesis failure |

---

## 5. How to run

### Prerequisites (macOS)

- Python **3.10** (tested; 3.14 on system won't work — use venv)
- Node.js 18+
- Optional: `brew install espeak-ng` (Kokoro falls back to `espeakng-loader` wheel)

### First-time setup

```bash
# Backend
cd backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # one-time, ~13 MB

# Frontend
cd frontend
npm install
```

### Daily dev

```bash
# Terminal 1
cd backend && source .venv/bin/activate
OMP_NUM_THREADS=1 uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv/*'

# Terminal 2
cd frontend && npm run dev
```

Open **http://localhost:5173** (use `localhost`, not `127.0.0.1` — Vite binds to localhost).

### Run tests

```bash
cd backend && source .venv/bin/activate && pytest        # 18 tests, ~0.04s
cd frontend && npm test                                  # 4 tests
```

---

## 6. Design decisions & history

### Why Kokoro (and not Chatterbox)

The project explored two engines:

| | Kokoro-82M | Chatterbox (removed) |
|---|---|---|
| Speed on Mac CPU | Near real-time | 30–90+ sec per sentence |
| Model size | ~200 MB | ~1–2 GB |
| RAM pressure | Low | High (process killed with exit 137) |
| Voices | 11 built-in narrators | Default only (cloning not implemented) |

**Chatterbox was removed** after testing — too slow and memory-heavy for local use on Mac. All Chatterbox code, deps, and UI have been deleted.

### Other decisions

- **Python 3.10 venv** — best wheel compatibility for Kokoro + PyTorch on macOS ARM
- **`create_app(preload_on_startup=False)`** — lets pytest run without loading models
- **500-char demo cap** — keeps first tests fast; raise `MAX_TEXT_LENGTH` in `base.py` when adding audiobook chunking
- **`OMP_NUM_THREADS=1`** — avoids OpenMP SHM errors in some sandbox/restricted environments
- **`--reload-exclude '.venv/*'`** — prevents uvicorn from restarting when pip installs packages mid-dev

---

## 7. Known issues & gotchas

1. **First run downloads models** from Hugging Face (~200 MB for Kokoro-82M). Subsequent runs use cache.
2. **Backend `--reload` during model load** restarts the process and re-downloads/re-loads. Use plain `uvicorn` (no `--reload`) while waiting for first model load.
3. **Process exit 137** = SIGKILL, usually OOM when running heavy models. Kokoro-only is much safer than the old dual-engine setup.
4. **Vite on `localhost` only** — curl to `127.0.0.1:5173` may fail; use `localhost:5173`.
5. **No git repo yet** — consider `git init` before next major change.
6. **Chatterbox packages may still be in `.venv`** from earlier install — harmless but bloated. Fresh venv with current `requirements.txt` is leaner.

---

## 8. What's NOT built yet (future work)

These were discussed but explicitly out of scope for the demo:

- [ ] Audiobook library shelf (EPUB/PDF import)
- [ ] Chapter navigation, resume position, playback speed
- [ ] Long-text chunking + audio stitching for full books
- [ ] Background job queue for synthesis
- [ ] Persistent audio cache on disk
- [ ] Kokoro voice blending (e.g. `af_sky+af_bella`)
- [ ] Desktop packaging (Tauri/Electron)
- [ ] Multi-tab UI (library vs. test vs. settings)

The **test tab** (`frontend/src/App.tsx`) is the foundation — dark Audible-inspired theme, ready to grow into a tabbed layout.

---

## 9. Suggested next steps (priority order)

1. **Initialize git** and commit current working state
2. **Tab shell** — wrap App in a layout with "Test" tab (current UI) and placeholder tabs for Library/Settings
3. **Long text support** — chunk text by sentence in `kokoro.py` (KPipeline already yields per-sentence chunks), stitch WAVs server-side
4. **File upload** — accept `.txt` / `.epub`, extract text, feed to chunker
5. **Playback UX** — speed control, scrubber persistence, queue next chapter

---

## 10. Environment notes (Roger's machine)

- macOS (darwin), Apple Silicon
- System Python: 3.14 (do not use directly)
- Project venv: Python 3.10.18 at `backend/.venv`
- Kokoro runs on **CPU** (fast enough for demo)

---

## 11. Quick verification checklist

After pulling or setting up on a new machine:

```bash
# 1. Backend health
curl -s http://localhost:8000/api/health | python3 -m json.tool
# Expect: "model_loaded": true

# 2. Synthesis
curl -s -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello from Speaking.","voice":"af_heart"}' \
  --output /tmp/test.wav && file /tmp/test.wav
# Expect: RIFF WAVE audio

# 3. Tests
cd backend && pytest -q && cd ../frontend && npm test
# Expect: 18 passed, 4 passed

# 4. UI
# Open http://localhost:5173 → enter text → Read → audio plays
```

---

*End of handoff.*
