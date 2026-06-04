import { useCallback, useEffect, useState } from 'react'
import {
  fetchBook,
  fetchBooks,
  fetchChapter,
  type BookDetail,
  type BookSummary,
  type ChapterDetail,
} from './api'
import { usePageAudio } from './hooks/usePageAudio'
import PageTextView from './PageTextView'
import type { HealthState } from './useHealth'

const DEFAULT_VOICE = 'af_heart'

function pageText(chapter: ChapterDetail | null): string {
  if (!chapter) return ''
  return chapter.chunks.map((c) => c.text).join('\n\n')
}

interface ReadTabProps {
  health: HealthState | null
}

export default function ReadTab({ health }: ReadTabProps) {
  const [books, setBooks] = useState<BookSummary[]>([])
  const [bookId, setBookId] = useState<number | null>(null)
  const [chapterId, setChapterId] = useState<number | null>(null)
  const [bookDetail, setBookDetail] = useState<BookDetail | null>(null)
  const [chapterDetail, setChapterDetail] = useState<ChapterDetail | null>(null)
  const [tocOpen, setTocOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [pageLoading, setPageLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [voice, setVoice] = useState(DEFAULT_VOICE)

  const {
    audioRef,
    phase,
    error: audioError,
    progress,
    chunkCount,
    generate,
    playAll,
    stop,
    reset: resetAudio,
    hasAudio,
  } = usePageAudio()

  const voices = health?.voices ?? []
  const modelReady = health?.modelLoaded ?? false
  const chapters = bookDetail?.chapters ?? []
  const chapterIndex =
    chapterId == null ? -1 : chapters.findIndex((c) => c.id === chapterId)
  const text = pageText(chapterDetail)
  const busy = phase === 'generating' || phase === 'playing'

  useEffect(() => {
    if (voices.length && !voices.includes(voice)) {
      setVoice(voices[0])
    }
  }, [voices, voice])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)

    fetchBooks()
      .then((data) => {
        if (!active) return
        setBooks(data)
        if (data.length > 0) {
          setBookId((prev) => prev ?? data[0].id)
        }
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load library')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (bookId == null) {
      setBookDetail(null)
      return
    }

    let active = true
    setError(null)

    fetchBook(bookId)
      .then((data) => {
        if (!active) return
        setBookDetail(data)
        setChapterId((prev) => {
          if (prev && data.chapters.some((c) => c.id === prev)) return prev
          return data.chapters[0]?.id ?? null
        })
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load book')
      })

    return () => {
      active = false
    }
  }, [bookId])

  useEffect(() => {
    if (bookId == null || chapterId == null) {
      setChapterDetail(null)
      return
    }

    let active = true
    setPageLoading(true)
    setError(null)

    fetchChapter(bookId, chapterId)
      .then((data) => {
        if (!active) return
        setChapterDetail(data)
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load page')
      })
      .finally(() => {
        if (active) setPageLoading(false)
      })

    return () => {
      active = false
    }
  }, [bookId, chapterId])

  useEffect(() => {
    resetAudio()
  }, [chapterId, resetAudio])

  const goToChapter = useCallback((index: number) => {
    const chapter = chapters[index]
    if (chapter) {
      setChapterId(chapter.id)
      setTocOpen(false)
    }
  }, [chapters])

  const goPrev = useCallback(() => {
    if (chapterIndex > 0) goToChapter(chapterIndex - 1)
  }, [chapterIndex, goToChapter])

  const goNext = useCallback(() => {
    if (chapterIndex >= 0 && chapterIndex < chapters.length - 1) {
      goToChapter(chapterIndex + 1)
    }
  }, [chapterIndex, chapters.length, goToChapter])

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const tag = (event.target as HTMLElement)?.tagName
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return

      if (event.key === 'Escape') {
        setTocOpen(false)
        return
      }
      if (event.key === 'ArrowLeft') {
        event.preventDefault()
        goPrev()
      }
      if (event.key === 'ArrowRight') {
        event.preventDefault()
        goNext()
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [goPrev, goNext])

  const handleGenerate = () => {
    if (!text.trim() || !modelReady || busy) return
    void generate(text, voice)
  }

  const handlePlay = () => {
    if (!hasAudio || busy) return
    if (phase === 'playing') {
      stop()
      return
    }
    void playAll()
  }

  const selectedBook = books.find((b) => b.id === bookId)

  return (
    <div className="relative flex min-h-[70svh] flex-col">
      <audio ref={audioRef} className="hidden" />

      {/* Page list drawer */}
      {tocOpen && bookDetail && (
        <>
          <button
            type="button"
            aria-label="Close page list"
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            onClick={() => setTocOpen(false)}
          />
          <aside className="fixed left-0 top-0 z-50 flex h-full w-72 max-w-[85vw] flex-col border-r border-gray-800 bg-[#161b22] shadow-2xl">
            <div className="border-b border-gray-800 px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-wider text-gray-500">
                Pages
              </p>
              <p className="mt-1 truncate font-medium text-white">
                {bookDetail.title}
              </p>
            </div>
            <nav className="flex-1 overflow-y-auto p-2">
              {chapters.map((chapter, i) => (
                <button
                  key={chapter.id}
                  type="button"
                  onClick={() => goToChapter(i)}
                  className={`mb-1 w-full rounded-lg px-3 py-2.5 text-left text-sm transition ${
                    chapter.id === chapterId
                      ? 'bg-amber-600/20 text-amber-200 ring-1 ring-amber-600/40'
                      : 'text-gray-300 hover:bg-white/5'
                  }`}
                >
                  {chapter.title}
                </button>
              ))}
            </nav>
          </aside>
        </>
      )}

      {/* Toolbar */}
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setTocOpen((o) => !o)}
          disabled={!bookDetail}
          aria-expanded={tocOpen}
          aria-label="Page list"
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-gray-700 bg-[#161b22] text-gray-300 transition hover:border-gray-600 hover:text-white disabled:opacity-40"
        >
          <ListIcon />
        </button>

        <select
          value={bookId ?? ''}
          onChange={(e) => {
            const id = Number(e.target.value)
            setBookId(id || null)
            setChapterId(null)
          }}
          disabled={books.length === 0}
          className="min-w-0 flex-1 rounded-xl border border-gray-700 bg-[#161b22] px-3 py-2 text-sm text-gray-100 focus:border-amber-500/60 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
        >
          {books.length === 0 && <option value="">No books</option>}
          {books.map((book) => (
            <option key={book.id} value={book.id}>
              {book.title}
            </option>
          ))}
        </select>

        {voices.length > 0 && (
          <select
            value={voice}
            onChange={(e) => setVoice(e.target.value)}
            aria-label="Voice"
            className="w-36 rounded-xl border border-gray-700 bg-[#161b22] px-3 py-2 text-sm text-gray-100 focus:border-amber-500/60 focus:outline-none focus:ring-2 focus:ring-amber-500/20"
          >
            {voices.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        )}
      </div>

      {(error || audioError) && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-300"
        >
          {error ?? audioError}
        </div>
      )}

      {loading && (
        <p className="py-12 text-center text-sm text-gray-500">Loading library…</p>
      )}

      {!loading && books.length === 0 && (
        <p className="py-12 text-center text-sm text-gray-500">
          No books yet. Import a PDF in the Library tab, then return here to read.
        </p>
      )}

      {!loading && books.length > 0 && (
        <>
          <div className="mb-3 flex items-center justify-between text-xs text-gray-500">
            <span className="truncate text-gray-400">
              {selectedBook?.author ? `${selectedBook.author} · ` : ''}
              {chapterDetail?.title ?? '—'}
            </span>
            {chapters.length > 0 && chapterIndex >= 0 && (
              <span>
                {chapterIndex + 1} / {chapters.length}
              </span>
            )}
          </div>

          {/* Ebook page */}
          <div className="relative flex-1">
            <div
              className={`mx-auto max-w-2xl rounded-sm bg-[#f4f1ea] px-6 py-10 shadow-[0_8px_40px_rgba(0,0,0,0.45),inset_0_1px_0_rgba(255,255,255,0.6)] sm:px-10 sm:py-14 min-h-[420px] ${
                pageLoading ? 'opacity-60' : ''
              }`}
            >
              {pageLoading && !chapterDetail ? (
                <p className="text-center font-serif text-stone-500">Loading page…</p>
              ) : (
                <PageTextView text={text} variant="reader" />
              )}
            </div>
          </div>

          {/* Controls */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={goPrev}
              disabled={chapterIndex <= 0}
              aria-label="Previous page"
              className="flex h-11 w-11 items-center justify-center rounded-full border border-gray-700 bg-[#161b22] text-gray-300 transition hover:border-gray-600 hover:text-white disabled:opacity-30"
            >
              <ChevronLeftIcon />
            </button>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={!text.trim() || !modelReady || busy}
              className="flex min-w-34 items-center justify-center gap-2 rounded-full bg-amber-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {phase === 'generating' ? (
                <>
                  <Spinner />
                  {progress
                    ? `${progress.done}/${progress.total}`
                    : 'Generating…'}
                </>
              ) : (
                <>
                  <WaveIcon />
                  Generate
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handlePlay}
              disabled={!hasAudio && phase !== 'playing'}
              className="flex min-w-34 items-center justify-center gap-2 rounded-full border border-gray-600 bg-[#161b22] px-5 py-2.5 text-sm font-medium text-gray-100 transition hover:border-gray-500 hover:bg-[#1c2128] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {phase === 'playing' ? (
                <>
                  <StopIcon />
                  Stop
                </>
              ) : (
                <>
                  <PlayIcon />
                  Play
                  {chunkCount > 1 ? ` (${chunkCount})` : ''}
                </>
              )}
            </button>

            <button
              type="button"
              onClick={goNext}
              disabled={chapterIndex < 0 || chapterIndex >= chapters.length - 1}
              aria-label="Next page"
              className="flex h-11 w-11 items-center justify-center rounded-full border border-gray-700 bg-[#161b22] text-gray-300 transition hover:border-gray-600 hover:text-white disabled:opacity-30"
            >
              <ChevronRightIcon />
            </button>
          </div>

          <p className="mt-4 text-center text-xs text-gray-600">
            ← → arrow keys · Esc closes page list
          </p>
        </>
      )}
    </div>
  )
}

function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
  )
}

function ListIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 6h16M4 12h16M4 18h16"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}

function ChevronLeftIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M15 18l-6-6 6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function ChevronRightIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M9 18l6-6-6-6"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

function PlayIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <path d="M8 5v14l11-7z" />
    </svg>
  )
}

function StopIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden>
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  )
}

function WaveIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M4 12c2-4 4-4 6 0s4 4 6 0M14 12c2-4 4-4 6 0"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
      />
    </svg>
  )
}
