# Speaking — Handoff Document

**Date:** June 4, 2026  
**Workspace:** `/Users/roger/Speaking`  
**Status:** Kokoro TTS demo + PDF library import/manage on Aiven Postgres

---

## 1. Project goal

Build a **local, Audible-style text-to-speech app** that runs entirely on-device — no cloud TTS API keys, no usage caps. The long-term vision is a personal audiobook reader (library, chapters, playback controls).

**What exists today:**

- **Test tab** — paste text (≤9000 chars), pick voice, synthesize to WAV in browser
- **Library tab** — import PDFs, shelf, per-page text preview (imprint + reflowed body)

**Planned platforms:** Mac/web app now → native iOS app later (see [`iOSPlan.md`](iOSPlan.md)). Audio sync via iCloud; **text and metadata in Postgres**.

---

## 2. Current state (what works)

| Area | Status |
|------|--------|
| Backend API | ✅ FastAPI on port 8000 |
| TTS engine | ✅ Kokoro-82M (Apache 2.0) |
| Frontend | ✅ Vite + React + Tailwind |
| Tabs | ✅ **Test** + **Library** + **Read** (ebook reader) |
| Voice picker | ✅ 11 built-in Kokoro voices |
| Database | ✅ SQLAlchemy + Alembic on Aiven (SQLite fallback) |
| PDF import | ✅ Per-page extract + TTS-oriented text cleanup |
| Library UI | ✅ Shelf, book pages, text preview, delete book/page |
| Audio cache (infra) | ✅ `AudioCache` class + DB index (no API routes yet) |
| Unit tests | ✅ 54 backend (pytest) + 10 frontend (vitest) |
| Regression PDF | ✅ `backend/tests/The Inner Game*.pdf` |

**Verified behavior:**

- Kokoro loads on CPU in ~5–10 s after first Hugging Face download
- Health polling until `model_loaded: true`
- PDF → one DB chapter per page, one `text_chunk` per page
- Page text format: **imprint lines** (`\n`-separated) + blank line + **reflowed body** (`\n\n` paragraphs)
- Aiven TLS via `certs/ca.pem` + `sslmode=require` (see `backend/.env.example`)
- `uvicorn --reload` for backend dev

**Not built yet (next agent):**

- Server-side chunk stitch + audio cache API for long pages
- Reading progress persistence
- Settings tab, reading progress, audio cache API

---

## 3. Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (localhost:5173)                    │
│  ├── Test tab      → POST /api/synthesize   │
│  ├── Library tab   → import / shelf / preview │
│  └── Read tab      → library + synthesize   │
└──────────────────┬──────────────────────────┘
                   │ /api/* proxied to :8000
                   ▼
┌─────────────────────────────────────────────┐
│  Backend (localhost:8000)                   │
│  ├── app/tts/kokoro.py                      │
│  ├── app/library/                           │
│  │   ├── pdf_extract.py  → pymupdf + clean  │
│  │   ├── text_clean.py   → imprint + body   │
│  │   ├── service.py      → DB import        │
│  │   ├── routes.py       → REST             │
│  │   └── audio_cache.py                     │
│  └── app/db/ → Postgres / SQLite            │
└──────────────────┬──────────────────────────┘
                   ▼
              Aiven PostgreSQL
```

### Key files

```
Speaking/
├── HANDOFF.md
├── backend/
│   ├── .env / .env.example
│   ├── certs/ca.pem          ← Aiven CA (gitignored)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py         ← DATABASE_URL, SSL for asyncpg
│   │   ├── schemas.py
│   │   ├── db/models.py
│   │   └── library/
│   │       ├── pdf_extract.py
│   │       ├── text_clean.py
│   │       ├── service.py
│   │       └── routes.py
│   └── tests/
│       ├── fixtures/inner_game.py   ← golden page-1 header
│       └── The Inner Game*.pdf      ← regression fixture
└── frontend/src/
    ├── App.tsx               ← tab shell
    ├── TestTab.tsx
    ├── ReadTab.tsx           ← ebook reader + playback
    ├── LibraryTab.tsx
    ├── PageTextView.tsx
    ├── lib/pageText.ts       ← split imprint vs body for display
    └── api/                  ← health, tts, library (+ api.ts re-exports)
```

---

## 4. API reference

### TTS

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Model status + voices |
| POST | `/api/synthesize` | JSON `{text, voice}` → `audio/wav` (max 9000 chars) |

### Library

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/library/import` | Multipart PDF → DB |
| GET | `/api/library/books` | Shelf list |
| GET | `/api/library/books/{id}` | Book + page list |
| GET | `/api/library/books/{id}/chapters/{id}` | Page text (one chunk) |
| DELETE | `/api/library/books/{id}` | Remove book |
| DELETE | `/api/library/books/{id}/chapters/{id}` | Remove page |

### Page text format (stored in `text_chunks.text`)

```
The Inner Game
of Tennis
W Timothy Gallwey
Jonathan Cape
Thirty-two Bedford Square London

Every game is composed of two parts, an outer game and an inner game. …
```

- **Imprint block:** single `\n` between lines (TTS pauses between title/author lines)
- **Body:** `\n\n` between paragraphs; no soft-wrap `\n` mid-sentence
- Cleanup in `text_clean.py` (hyphen join, punctuation heuristics, body-start detection)

Golden header constant: `tests/fixtures/inner_game.py` → `INNER_GAME_PAGE1_HEADER`

---

## 5. Database

- **Models:** `Book` → `Chapter` (one per PDF page) → `TextChunk` (one per page today)
- **Also:** `reading_progress`, `audio_cache_index` (unused by UI)
- **Migrations:** `cd backend && alembic upgrade head`
- **Aiven:** `postgresql+asyncpg://…?sslmode=require` + `backend/certs/ca.pem`

---

## 6. How to run

```bash
# Backend
cd backend && source .venv/bin/activate
pip install -r requirements.txt   # includes pymupdf
cp .env.example .env              # DATABASE_URL + optional DATABASE_SSL_CA
alembic upgrade head
OMP_NUM_THREADS=1 uvicorn app.main:app --reload --port 8000 --reload-exclude '.venv/*'

# Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** (not `127.0.0.1`).

### Tests

```bash
cd backend && pytest -q                    # 54 tests
cd frontend && npm test -- --run         # 10 tests
pytest tests/test_inner_game_pdf.py -v   # PDF regression only
```

---

## 7. Design decisions

| Topic | Decision |
|-------|----------|
| TTS engine | Kokoro-82M on CPU (Chatterbox removed — too slow/OOM) |
| PDF storage | One chapter = one page; one text chunk per page (for now) |
| Text cleanup | `text_clean.py` — imprint vs body; not 500-char chunking at import |
| asyncpg + Aiven | Strip `sslmode` from URL; `ssl=True` or CA file via `resolve_ssl_ca_path()` |
| Frontend API | Split `api/health.ts`, `api/tts.ts`, `api/library.ts`; barrel `api.ts` |
| Display | `PageTextView` + `splitPageText()` — HTML must not collapse imprint `\n` |

---

## 8. Known gotchas

1. First Kokoro run downloads ~200 MB from Hugging Face.
2. **`--reload` during model load** can restart mid-download — wait or run without reload once.
3. **Re-import PDFs** after text-cleaner changes; old DB rows keep prior formatting.
4. Vite binds **localhost** only.
5. Aiven free tier may sleep — wake in console.
6. **405 on DELETE** — stale uvicorn process without `--reload`; restart backend.

---

## 9. What's NOT built yet

- [x] **Read tab** — ebook UI, page list, prev/next, generate/play audio (9000-char limit)
- [ ] Library TTS playback (synthesize page/paragraph, play in browser)
- [ ] Raise `MAX_TEXT_LENGTH`; optional `chunking.py` for long TTS requests
- [ ] `reading_progress`, audio cache routes
- [ ] Settings tab
- [ ] EPUB import, desktop packaging, iOS app

---

## 10. Next steps (for next agent)

### Phase B — Read tab ✅ (done)

- Tab: Test | Library | **Read**
- Ebook-style single page, expandable page list, ←/→ navigation + arrow keys
- Generate / Play via `POST /api/synthesize` (up to 9000 chars per request; client chunks above that)

### Phase C — Listening polish

1. Server-side chunk + stitch in `kokoro.py`; audio cache routes
2. Persist `reading_progress`

---

## 11. Environment (Roger)

- macOS Apple Silicon, Python **3.10** venv at `backend/.venv`
- Aiven: **bookie** / `pg-main-bookie`, CA at `backend/certs/ca.pem`
- Do not use system Python 3.14 for this project

---

## 12. Quick verification

```bash
curl -s http://localhost:8000/api/health | python3 -m json.tool
curl -s -X POST http://localhost:8000/api/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello.","voice":"af_heart"}' --output /tmp/t.wav
cd backend && pytest -q && cd ../frontend && npm test -- --run
```

---

*End of handoff.*
