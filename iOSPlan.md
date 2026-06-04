# Speaking — iOS Plan

**Status:** Planning (implement after core Mac Kokoro + library features are ready)  
**Target device:** iPhone 11+ (playback-first; synthesis on Mac)  
**Storage:** 2 TB iCloud family plan — audio via CloudKit; text in a database

---

## 1. Goal

Ship a native **Swift iOS app** that works like Audible for books imported on Mac:

- **Mac** imports PDF/EPUB, extracts text, synthesizes with Kokoro, uploads compressed audio to iCloud
- **iPhone** syncs library metadata + audio, plays offline, resumes where you left off
- **Database** holds text, structure, and progress — never audio bytes
- **iCloud (CloudKit)** holds AAC chapter files and syncs them across your Apple ID

No cloud TTS API keys. No usage caps. User pays only for their existing iCloud storage.

---

## 2. Prerequisites (Mac core must be done first)

Do not start iOS until these Mac/web milestones exist:

| # | Mac milestone | Why iOS needs it |
|---|---------------|------------------|
| 1 | Long-text chunking + WAV synthesis | Defines chunk boundaries iOS plays |
| 2 | PDF/EPUB import + text extraction | Populates DB text that Mac syncs |
| 3 | Library UI (shelf, chapters) | UX parity; CloudKit schema mirrors this |
| 4 | Reading progress persisted in DB | Same model syncs to iPhone |
| 5 | AAC transcode pipeline (WAV → `.m4a`) | Reasonable iCloud upload sizes |
| 6 | Native Mac app or signed helper with CloudKit entitlements | Python FastAPI cannot write to iCloud directly |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Mac (synthesis hub)                                            │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────────────┐  │
│  │ Import       │──▶│ SQLite/     │──▶│ Kokoro → WAV → AAC   │  │
│  │ PDF/EPUB     │   │ Postgres DB │   │ per text chunk       │  │
│  └──────────────┘   │ (text only) │   └──────────┬───────────┘  │
│                     └──────┬──────┘              │              │
│                            │                     ▼              │
│                     Swift Mac app                 CloudKit upload│
│                     (CKSyncEngine)              (CKAsset .m4a) │
└────────────────────────────┬────────────────────────────────────┘
                             │  same Apple ID, private CloudKit DB
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  iPhone (playback client)                                       │
│  ┌──────────────┐   ┌─────────────┐   ┌──────────────────────┐  │
│  │ CKSyncEngine │──▶│ GRDB/SQLite │──▶│ AVAudioEngine player │  │
│  │ download     │   │ local cache │   │ + lock screen controls│  │
│  └──────────────┘   │ text+meta   │   └──────────────────────┘  │
│                     │ AAC files   │                             │
│                     └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Division of responsibility

| Layer | Stores | Does not store |
|-------|--------|----------------|
| **Database** (Mac + iPhone local) | Book metadata, chapters, text chunks, reading progress, audio file pointers | Audio bytes |
| **CloudKit** | AAC files as `CKAsset`, sync metadata (voice, duration, chunk UUID) | Raw PDF binaries (optional; see §6) |
| **Device cache** | Downloaded `.m4a` files, temp WAV during Mac synthesis | — |

---

## 4. Why keep text in a database

Text in a DB (not flat files or CloudKit records alone) is the right call:

1. **Structured queries** — "resume book 7", "list unfinished", "find chunk by index"
2. **Small footprint** — ~1 MB per book vs ~280 MB AAC; cheap to sync metadata often
3. **Chunk alignment** — TTS chunk boundaries match DB rows; playback maps 1:1
4. **Already started** — Mac backend has `books`, `chapters`, `text_chunks`, `reading_progress`, `audio_cache_index` in [`backend/app/db/models.py`](backend/app/db/models.py)
5. **Offline search** (future) — full-text search over titles/chapters without parsing files
6. **Re-synthesis** — if you change voice or Kokoro version, text is the source of truth; regenerate AAC from chunks

CloudKit syncs **audio + lightweight record fields**. The iPhone keeps a **local SQLite copy** of text (via GRDB or SwiftData) populated from CloudKit metadata records or a one-time Mac push.

---

## 5. Data model

### 5.1 Mac backend (existing — extend as needed)

Already defined in Python/SQLAlchemy:

```
books
  └── chapters
        └── text_chunks          ← plain text, 500–2000 chars each
              └── audio_cache_index  ← local path + cloud asset ID (never bytes)

reading_progress  ← one row per book (chapter, chunk, char_offset, voice)
```

**Mac additions before iOS:**

- `text_chunks.cloudkit_record_id` (UUID string) — stable ID across devices
- `audio_cache_index.format` — `wav` | `aac`
- `audio_cache_index.duration_ms`
- `audio_cache_index.cloudkit_asset_record_id`
- `books.sync_state` — `local` | `uploading` | `synced` | `error`

### 5.2 CloudKit schema (private database)

Use **separate record types** so updating progress does not re-upload audio.

| Record type | Fields | Asset |
|-------------|--------|-------|
| `Book` | `title`, `author`, `sourceType`, `pageCount`, `createdAt`, `bookUUID` | — |
| `Chapter` | `bookUUID`, `title`, `sortOrder`, `chapterUUID` | — |
| `TextChunk` | `chapterUUID`, `chunkIndex`, `text`, `chunkUUID` | — |
| `AudioChunk` | `chunkUUID`, `voice`, `durationMs`, `fileSizeBytes`, `codec` (`aac`) | **CKAsset** (`.m4a`) |
| `ReadingProgress` | `bookUUID`, `chapterUUID`, `chunkUUID`, `charOffset`, `voice`, `updatedAt` | — |

**Rules:**

- One `AudioChunk` record per `(chunkUUID, voice)` — same as `audio_cache_index` unique constraint
- Store `chunkUUID` as the cross-platform foreign key (not Mac auto-increment IDs)
- Text lives in `TextChunk` CloudKit records **and** local DB on both devices

### 5.3 iPhone local database (GRDB or SwiftData)

Mirror the Mac schema. Populate via `CKSyncEngine` fetch on launch + push notification.

Recommended: **GRDB** for explicit control and easy migration from Mac schema; SwiftData is fine if you prefer Apple-native APIs.

---

## 6. Audio pipeline

### 6.1 Synthesis (Mac only)

1. Read `text_chunks.text` from DB
2. Synthesize with Kokoro → 24 kHz mono WAV (existing [`backend/app/tts/kokoro.py`](backend/app/tts/kokoro.py))
3. Write WAV to `backend/data/audio_cache/` (existing [`backend/app/library/audio_cache.py`](backend/app/library/audio_cache.py))
4. Transcode WAV → AAC (see §6.2)
5. Upload AAC as `CKAsset`; save `cloudkit_asset_record_id` in `audio_cache_index`
6. Optionally delete Mac WAV after successful upload (keep AAC locally)

### 6.2 AAC transcode settings

| Setting | Value | Rationale |
|---------|-------|-----------|
| Codec | AAC-LC in `.m4a` container | Native iOS; best Apple ecosystem support |
| Bitrate | **64 kbps** mono | ~280 MB per 10 hr book; transparent for speech |
| Sample rate | 24 kHz | Matches Kokoro output; no upsampling needed |
| Tool (Mac) | `afconvert` (built-in) or FFmpeg | `afconvert -f m4af -d aac -b 64000 input.wav output.m4a` |

### 6.3 Storage estimates (2 TB family plan)

| Book size | AAC (~64 kbps) | WAV (don't upload) |
|-----------|----------------|---------------------|
| ~350 pages / ~10 hr | **~280 MB** | ~1.7 GB |
| ~500 pages / ~14 hr | **~390 MB** | ~2.4 GB |

At 280 MB/book, even 200 GB of family iCloud headroom holds **~700 books** as AAC.

---

## 7. Sync strategy

### 7.1 Mac → CloudKit (upload)

Use **CKSyncEngine** (iOS 17+ / macOS 14+) in a native Swift Mac app:

1. After import + chunking: push `Book`, `Chapter`, `TextChunk` records
2. Background queue: synthesize + transcode + upload `AudioChunk` one chapter at a time
3. Debounce progress updates (3 s) — do not upload on every scrub tick
4. Persist `stateSerialization` to disk for crash recovery

### 7.2 CloudKit → iPhone (download)

1. `CKSyncEngine` fetch on app launch and when receiving CloudKit push
2. Download `TextChunk` + metadata immediately (small)
3. Download `AudioChunk` assets on demand:
   - **"Download book"** — all chapters over Wi‑Fi
   - **Stream next chapter** — prefetch current + next while playing
4. Save AAC to `Library/Caches/Speaking/audio/{chunkUUID}.m4a`
5. Update local DB `audio_cache_index` equivalent with local path

### 7.3 Reading progress (bidirectional)

- iPhone updates `ReadingProgress` CloudKit record on pause / chapter change
- Mac syncs progress back for web UI consistency
- Last-write-wins on `updatedAt` is acceptable for single-user personal app

---

## 8. iOS app structure

```
SpeakingIOS/
├── App/
│   ├── SpeakingApp.swift
│   └── AppDelegate.swift          # CloudKit remote notifications
├── Library/
│   ├── LibraryView.swift          # Audible-style shelf
│   ├── BookDetailView.swift
│   └── ChapterListView.swift
├── Player/
│   ├── PlayerView.swift
│   ├── PlayerViewModel.swift
│   └── NowPlayingInfoCenter.swift # Lock screen + CarPlay
├── Sync/
│   ├── CloudKitSyncEngine.swift   # CKSyncEngine delegate
│   ├── SyncCoordinator.swift
│   └── DownloadManager.swift      # Wi‑Fi/cellular policy
├── Database/
│   ├── Models.swift               # Mirror Mac schema
│   ├── DatabaseManager.swift      # GRDB
│   └── Migrations/
└── Resources/
    └── Assets.xcassets
```

### Minimum iOS version

- **iOS 17+** — `CKSyncEngine`, modern SwiftUI
- iPhone 11 supports iOS 17/18

### Playback stack

- `AVAudioPlayer` or `AVAudioEngine` for AAC files
- `MPNowPlayingInfoCenter` + `MPRemoteCommandCenter` for lock screen
- Background audio capability in entitlements

---

## 9. iPhone 11 and fallbacks

| Capability | iPhone 11 approach |
|--------------|-------------------|
| **Primary playback** | Downloaded AAC from iCloud — no synthesis needed |
| **Instant preview** | `AVSpeechSynthesizer` (built-in) for ad-hoc text — lower quality, zero upload wait |
| **On-device Kokoro** | Optional v2 — CoreML ports exist (`speech-swift`, `kokoro-coreml`); benchmark on A13 before committing |
| **Cellular downloads** | Default off; prompt "Download over Wi‑Fi?" |

The v1 iPhone app is a **player**, not a synthesizer. Mac does the heavy work.

---

## 10. Mac ↔ iOS integration options

The Python FastAPI backend **cannot** access CloudKit. Choose one:

| Option | Pros | Cons |
|--------|------|------|
| **A. Swift Mac menu-bar app** (recommended) | Native CloudKit; can shell out to Python for Kokoro or embed CoreML | New codebase |
| **B. Mac app + FastAPI IPC** | Reuses existing Python Kokoro | Two processes; more plumbing |
| **C. CoreML Kokoro in Mac Swift app** | Single native stack; same as future iOS synthesis | Port work from Python |

**Recommended:** Option A or C — one Swift Mac app with shared `SpeakingKit` framework used by iOS later.

Shared framework contains:

- CloudKit record types + sync engine wrapper
- GRDB models + migrations
- UUID scheme for cross-device IDs

Mac-specific: synthesis worker (Python subprocess or CoreML)  
iOS-specific: UI + player + download manager

---

## 11. Implementation phases

### Phase 0 — Mac core (blocking)

- [ ] Long-text chunking in Kokoro backend
- [ ] PDF/EPUB import → DB text chunks
- [ ] Library + playback UI on Mac/web
- [ ] AAC transcode after synthesis
- [ ] Stable `chunkUUID` on all rows

### Phase 1 — Mac CloudKit uploader

- [ ] Apple Developer account + iCloud container entitlement
- [ ] CloudKit schema deployed (Development → Production)
- [ ] Swift Mac app: import triggers upload queue
- [ ] Upload text records + AAC assets
- [ ] Verify records in CloudKit Console

### Phase 2 — iOS library + sync

- [ ] Xcode project, GRDB, CKSyncEngine
- [ ] Fetch books/chapters/text from CloudKit → local DB
- [ ] Library shelf UI (match Mac dark Audible theme)
- [ ] Manual "Download book" over Wi‑Fi

### Phase 3 — iOS playback

- [ ] Chapter player with scrubber
- [ ] Reading progress save → CloudKit
- [ ] Lock screen / Control Center controls
- [ ] Background audio

### Phase 4 — Polish

- [ ] Prefetch next chapter while playing
- [ ] Storage usage screen ("Using X MB of iCloud")
- [ ] Sync status indicators per book
- [ ] `AVSpeechSynthesizer` fallback for unread chunks
- [ ] Optional: on-device Kokoro CoreML benchmark on iPhone 11

---

## 12. Entitlements and App Store notes

- **iCloud** — CloudKit container `iCloud.com.<team>.speaking`
- **Background modes** — Audio, Remote notifications (CloudKit push)
- **Privacy** — No third-party analytics required; all data stays in user's iCloud private DB
- **Storage UX** — Show per-book AAC size before download; never silently fill family iCloud
- **App Store category** — Books or Entertainment

---

## 13. Open decisions (resolve before Phase 1)

| Decision | Options | Recommendation |
|----------|---------|----------------|
| iPhone local DB | GRDB vs SwiftData | GRDB — matches SQL schema, easier Mac parity |
| Mac synthesis | Python subprocess vs CoreML | Python first (reuse backend); CoreML later |
| PDF binary storage | iCloud Drive vs don't sync | Don't sync — re-import on new device if needed |
| Voice per book | Single voice vs per-chapter | Single voice per book (simpler sync) |
| Hosted Postgres | Aiven/Supabase vs SQLite only | SQLite + CloudKit for personal Apple-only v1; Postgres if web library later |

---

## 14. Success criteria

- [ ] Import a PDF on Mac; within minutes, book appears on iPhone library
- [ ] Download book over Wi‑Fi; play full chapter offline on iPhone 11
- [ ] Pause on iPhone; resume on Mac (or vice versa) within same chapter
- [ ] 350-page book uses ~280 MB iCloud (AAC), not ~1.7 GB (WAV)
- [ ] Text searchable in library without network
- [ ] No cloud API keys; no monthly TTS bill

---

## 15. References

- Mac DB models: [`backend/app/db/models.py`](backend/app/db/models.py)
- Audio cache (local disk, not DB): [`backend/app/library/audio_cache.py`](backend/app/library/audio_cache.py)
- Kokoro engine: [`backend/app/tts/kokoro.py`](backend/app/tts/kokoro.py)
- Apple: [CKSyncEngine](https://developer.apple.com/documentation/cloudkit/cksyncengine-5sie5) (WWDC23)
- Kokoro CoreML (optional): [speech-swift](https://github.com/soniqo/speech-swift), [kokoro-coreml](https://github.com/jud/kokoro-coreml)

---

*Implement this plan after Mac library + chunking + AAC transcode are working. iOS v1 is playback + sync, not on-device synthesis.*
