import { readApiError } from '../lib/apiError'

export interface BookSummary {
  id: number
  title: string
  author: string | null
  source_filename: string | null
  source_type: string
  page_count: number | null
  created_at: string
}

export interface ChapterSummary {
  id: number
  title: string
  sort_order: number
  chunk_count: number
}

export interface BookDetail extends BookSummary {
  chapters: ChapterSummary[]
}

export interface TextChunk {
  chunk_index: number
  text: string
}

export interface ChapterDetail {
  id: number
  book_id: number
  title: string
  sort_order: number
  chunks: TextChunk[]
}

export async function fetchBooks(): Promise<BookSummary[]> {
  const res = await fetch('/api/library/books')
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Failed to load books'))
  }
  return res.json()
}

export async function fetchBook(bookId: number): Promise<BookDetail> {
  const res = await fetch(`/api/library/books/${bookId}`)
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Failed to load book'))
  }
  return res.json()
}

export async function fetchChapter(
  bookId: number,
  chapterId: number,
): Promise<ChapterDetail> {
  const res = await fetch(
    `/api/library/books/${bookId}/chapters/${chapterId}`,
  )
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Failed to load page'))
  }
  return res.json()
}

export async function deleteBook(bookId: number): Promise<void> {
  const res = await fetch(`/api/library/books/${bookId}`, { method: 'DELETE' })
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Failed to delete book'))
  }
}

export async function deletePage(bookId: number, chapterId: number): Promise<void> {
  const res = await fetch(
    `/api/library/books/${bookId}/chapters/${chapterId}`,
    { method: 'DELETE' },
  )
  if (!res.ok) {
    throw new Error(await readApiError(res, 'Failed to delete page'))
  }
}

export async function importPdf(file: File): Promise<BookDetail> {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch('/api/library/import', {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    throw new Error(await readApiError(res, 'Import failed'))
  }
  return res.json()
}
