# Speaking

A local Audible-style text-to-speech app powered by [Kokoro](https://github.com/hexgrad/kokoro).

## Prerequisites (macOS)

- **Python 3.10+**
- **Node.js 18+**
- **espeak-ng** — `brew install espeak-ng` (Kokoro uses `espeakng-loader` on macOS if brew is unavailable)

## First-time setup

### Backend

```bash
cd backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # one-time
```

### Frontend

```bash
cd frontend
npm install
```

## Development

```bash
# Terminal 1 — backend (port 8000)
cd backend
source .venv/bin/activate
OMP_NUM_THREADS=1 uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv/*'

# Terminal 2 — frontend (port 5173)
cd frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173), enter text, pick a voice, and click **Read**.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | `{ status, model_loaded, voices, device }` |
| `/api/synthesize` | POST | `{ "text": "...", "voice": "af_heart" }` → `audio/wav` |

## Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pip install -r requirements-dev.txt && pytest

# Frontend
cd frontend && npm test
```

## First-run expectations

| Step | What happens |
|------|--------------|
| `pip install` | Downloads Kokoro + PyTorch deps |
| First synthesis | Kokoro-82M weights download (~200 MB) from Hugging Face |
| Subsequent reads | Near real-time on CPU |
