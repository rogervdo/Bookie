import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchBook,
  fetchBooks,
  deleteBook,
  fetchChapter,
  fetchHealth,
  importPdf,
  synthesize,
} from './api'

describe('fetchHealth', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns parsed health payload', async () => {
    const payload = {
      status: 'ok',
      model_loaded: true,
      loading: false,
      load_error: null,
      device: 'cpu',
      voices: ['af_heart'],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    )

    await expect(fetchHealth()).resolves.toEqual(payload)
    expect(fetch).toHaveBeenCalledWith('/api/health')
  })

  it('throws when backend is unavailable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        text: async () => 'Service unavailable',
      }),
    )

    await expect(fetchHealth()).rejects.toThrow('Service unavailable')
  })
})

describe('synthesize', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('posts text and voice to the API', async () => {
    const blob = new Blob(['audio'], { type: 'audio/wav' })

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => blob,
      }),
    )

    await expect(synthesize('Hello', 'af_heart')).resolves.toBe(blob)
    expect(fetch).toHaveBeenCalledWith('/api/synthesize', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: 'Hello', voice: 'af_heart' }),
    })
  })

  it('throws synthesis errors from the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        text: async () => 'Kokoro is still loading',
      }),
    )

    await expect(synthesize('Hello')).rejects.toThrow('Kokoro is still loading')
  })
})

describe('library API', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fetchBooks loads the shelf', async () => {
    const books = [
      {
        id: 1,
        title: 'Sample',
        author: 'Author',
        source_filename: 'sample.pdf',
        source_type: 'pdf',
        page_count: 1,
        created_at: '2026-06-04T00:00:00Z',
      },
    ]

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => books,
      }),
    )

    await expect(fetchBooks()).resolves.toEqual(books)
    expect(fetch).toHaveBeenCalledWith('/api/library/books')
  })

  it('fetchBook loads book detail', async () => {
    const book = {
      id: 1,
      title: 'Sample',
      author: null,
      source_filename: 'sample.pdf',
      source_type: 'pdf',
      page_count: 1,
      created_at: '2026-06-04T00:00:00Z',
      chapters: [{ id: 2, title: 'Content', sort_order: 0, chunk_count: 3 }],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => book,
      }),
    )

    await expect(fetchBook(1)).resolves.toEqual(book)
    expect(fetch).toHaveBeenCalledWith('/api/library/books/1')
  })

  it('fetchChapter loads chunked text', async () => {
    const chapter = {
      id: 2,
      book_id: 1,
      title: 'Content',
      sort_order: 0,
      chunks: [{ chunk_index: 0, text: 'Hello' }],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => chapter,
      }),
    )

    await expect(fetchChapter(1, 2)).resolves.toEqual(chapter)
    expect(fetch).toHaveBeenCalledWith('/api/library/books/1/chapters/2')
  })

  it('deleteBook sends DELETE', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true }),
    )

    await deleteBook(3)
    expect(fetch).toHaveBeenCalledWith('/api/library/books/3', {
      method: 'DELETE',
    })
  })

  it('importPdf uploads multipart form data', async () => {
    const file = new File(['pdf'], 'book.pdf', { type: 'application/pdf' })
    const imported = {
      id: 1,
      title: 'book',
      author: null,
      source_filename: 'book.pdf',
      source_type: 'pdf',
      page_count: 1,
      created_at: '2026-06-04T00:00:00Z',
      chapters: [],
    }

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => imported,
      }),
    )

    await expect(importPdf(file)).resolves.toEqual(imported)
    expect(fetch).toHaveBeenCalledWith('/api/library/import', {
      method: 'POST',
      body: expect.any(FormData),
    })
  })
})
