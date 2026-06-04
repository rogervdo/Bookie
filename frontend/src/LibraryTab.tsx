import { useCallback, useEffect, useRef, useState } from 'react'
import {
  deleteBook,
  deletePage,
  fetchBook,
  fetchBooks,
  fetchChapter,
  importPdf,
  type BookDetail,
  type BookSummary,
  type ChapterDetail,
} from './api'
import PageTextView from './PageTextView'

type LibraryView =
  | { kind: 'shelf' }
  | { kind: 'book'; bookId: number }
  | { kind: 'chapter'; bookId: number; chapterId: number }

export default function LibraryTab() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [view, setView] = useState<LibraryView>({ kind: 'shelf' })
  const [books, setBooks] = useState<BookSummary[]>([])
  const [bookDetail, setBookDetail] = useState<BookDetail | null>(null)
  const [chapterDetail, setChapterDetail] = useState<ChapterDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadShelf = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchBooks()
      setBooks(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load library')
    } finally {
      setLoading(false)
    }
  }, [])

  const reloadBook = useCallback(async (bookId: number) => {
    const data = await fetchBook(bookId)
    setBookDetail(data)
    return data
  }, [])

  useEffect(() => {
    if (view.kind === 'shelf') {
      void loadShelf()
    }
  }, [view.kind, loadShelf])

  useEffect(() => {
    if (view.kind !== 'book') {
      setBookDetail(null)
      return
    }

    let active = true
    setLoading(true)
    setError(null)

    fetchBook(view.bookId)
      .then((data) => {
        if (!active) return
        setBookDetail(data)
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load book')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [view])

  useEffect(() => {
    if (view.kind !== 'chapter') {
      setChapterDetail(null)
      return
    }

    let active = true
    setLoading(true)
    setError(null)

    fetchChapter(view.bookId, view.chapterId)
      .then((data) => {
        if (!active) return
        setChapterDetail(data)
      })
      .catch((err) => {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load page')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [view])

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelected = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return

    setImporting(true)
    setError(null)
    try {
      const imported = await importPdf(file)
      await loadShelf()
      setView({ kind: 'book', bookId: imported.id })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setImporting(false)
    }
  }

  const handleDeleteBook = async (bookId: number) => {
    if (!window.confirm('Remove this book from your library?')) return

    setDeletingId(bookId)
    setError(null)
    try {
      await deleteBook(bookId)
      if (view.kind !== 'shelf' && view.bookId === bookId) {
        setView({ kind: 'shelf' })
      }
      await loadShelf()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete book')
    } finally {
      setDeletingId(null)
    }
  }

  const handleDeletePage = async (bookId: number, chapterId: number) => {
    if (!window.confirm('Remove this page?')) return

    setDeletingId(chapterId)
    setError(null)
    try {
      await deletePage(bookId, chapterId)
      if (view.kind === 'chapter' && view.chapterId === chapterId) {
        setView({ kind: 'book', bookId })
      }
      const book = await reloadBook(bookId)
      if (book.chapters.length === 0) {
        await deleteBook(bookId)
        setView({ kind: 'shelf' })
        await loadShelf()
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete page')
    } finally {
      setDeletingId(null)
    }
  }

  const goToShelf = () => {
    setView({ kind: 'shelf' })
    setBookDetail(null)
    setChapterDetail(null)
  }

  return (
    <div className="rounded-2xl border border-gray-800 bg-[#161b22] p-6 shadow-xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          {view.kind !== 'shelf' && (
            <button
              type="button"
              onClick={goToShelf}
              className="mb-2 text-sm text-amber-400 hover:text-amber-300"
            >
              ← Library
            </button>
          )}
          <h2 className="text-lg font-medium text-white">
            {view.kind === 'shelf' && 'Your library'}
            {view.kind === 'book' && (bookDetail?.title ?? 'Book')}
            {view.kind === 'chapter' && (chapterDetail?.title ?? 'Page')}
          </h2>
        </div>

        <div className="flex items-center gap-2">
          {view.kind === 'book' && bookDetail && (
            <button
              type="button"
              onClick={() => handleDeleteBook(bookDetail.id)}
              disabled={deletingId === bookDetail.id}
              className="rounded-xl border border-red-900/60 px-4 py-2 text-sm text-red-300 hover:bg-red-950/40 disabled:opacity-50"
            >
              Delete book
            </button>
          )}
          {view.kind === 'shelf' && (
            <>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileSelected}
              />
              <button
                type="button"
                onClick={handleImportClick}
                disabled={importing}
                className="rounded-xl bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
              >
                {importing ? 'Importing…' : 'Import PDF'}
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg border border-red-900/50 bg-red-950/40 px-4 py-3 text-sm text-red-300"
        >
          {error}
        </div>
      )}

      {loading && <p className="text-sm text-gray-500">Loading…</p>}

      {!loading && view.kind === 'shelf' && (
        <div className="space-y-3">
          {books.length === 0 && (
            <p className="text-sm text-gray-500">
              No books yet. Import a PDF to extract text and add it to your shelf.
            </p>
          )}
          {books.map((book) => (
            <div
              key={book.id}
              className="flex items-stretch gap-2 rounded-xl border border-gray-700 bg-[#0f1419]"
            >
              <button
                type="button"
                onClick={() => setView({ kind: 'book', bookId: book.id })}
                className="min-w-0 flex-1 px-4 py-3 text-left transition hover:bg-white/[0.02]"
              >
                <span className="font-medium text-gray-100">{book.title}</span>
                {book.author && (
                  <span className="mt-1 block text-sm text-gray-400">
                    {book.author}
                  </span>
                )}
                <span className="mt-1 block text-xs text-gray-500">
                  {book.page_count != null ? `${book.page_count} pages · ` : ''}
                  {new Date(book.created_at).toLocaleDateString()}
                </span>
              </button>
              <button
                type="button"
                aria-label={`Delete ${book.title}`}
                onClick={() => handleDeleteBook(book.id)}
                disabled={deletingId === book.id}
                className="shrink-0 border-l border-gray-700 px-4 text-sm text-red-400 hover:bg-red-950/30 hover:text-red-300 disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {!loading && view.kind === 'book' && bookDetail && (
        <div className="space-y-3">
          {bookDetail.author && (
            <p className="text-sm text-gray-400">by {bookDetail.author}</p>
          )}
          {bookDetail.source_filename && (
            <p className="text-xs text-gray-500">{bookDetail.source_filename}</p>
          )}
          <p className="text-sm text-gray-500">
            {bookDetail.chapters.length} page
            {bookDetail.chapters.length === 1 ? '' : 's'}
          </p>
          {bookDetail.chapters.map((chapter) => (
            <div
              key={chapter.id}
              className="flex items-stretch gap-2 rounded-xl border border-gray-700 bg-[#0f1419]"
            >
              <button
                type="button"
                onClick={() =>
                  setView({
                    kind: 'chapter',
                    bookId: bookDetail.id,
                    chapterId: chapter.id,
                  })
                }
                className="min-w-0 flex-1 px-4 py-3 text-left text-gray-100 transition hover:bg-white/[0.02]"
              >
                {chapter.title}
              </button>
              <button
                type="button"
                aria-label={`Delete ${chapter.title}`}
                onClick={() => handleDeletePage(bookDetail.id, chapter.id)}
                disabled={deletingId === chapter.id}
                className="shrink-0 border-l border-gray-700 px-4 text-sm text-red-400 hover:bg-red-950/30 hover:text-red-300 disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {!loading && view.kind === 'chapter' && chapterDetail && (
        <div className="space-y-4">
          <button
            type="button"
            onClick={() =>
              setView({ kind: 'book', bookId: chapterDetail.book_id })
            }
            className="text-sm text-amber-400 hover:text-amber-300"
          >
            ← Back to book
          </button>
          <PageTextView text={chapterDetail.chunks.map((c) => c.text).join('\n\n')} />
        </div>
      )}
    </div>
  )
}
