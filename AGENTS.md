# Speaking — agent notes

Project handoff and architecture: see [HANDOFF.md](HANDOFF.md).

## Dev servers

```bash
# Backend (from backend/, Python 3.10 venv)
source .venv/bin/activate
OMP_NUM_THREADS=1 uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv/*'

# Frontend (from frontend/)
npm run dev
```

App UI: http://localhost:5173 · API: http://localhost:8000

## Tests

Run after backend or frontend changes. Use the project venv (`backend/.venv`, Python 3.10).

```bash
# All backend tests
cd backend && source .venv/bin/activate && pytest -q

# All frontend tests
cd frontend && npm test -- --run

# PDF regression only (requires backend/tests/The Inner Game*.pdf)
cd backend && source .venv/bin/activate && pytest tests/test_inner_game_pdf.py -v

# Full suite (from repo root)
cd backend && source .venv/bin/activate && pytest -q && cd ../frontend && npm test -- --run
```

Expected: **54** backend + **10** frontend tests passing.

## First-time backend setup

```bash
cd backend
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL; optional certs/ca.pem for Aiven
alembic upgrade head
```
