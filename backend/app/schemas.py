from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import Book, Chapter, TextChunk
from app.tts.base import MAX_TEXT_LENGTH


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH)
    voice: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    loading: bool
    load_error: Optional[str] = None
    device: Optional[str] = None
    voices: list[str] = []


class BookSummaryResponse(BaseModel):
    id: int
    title: str
    author: str | None
    source_filename: str | None
    source_type: str
    page_count: int | None
    created_at: datetime

    @classmethod
    def from_book(cls, book: Book) -> BookSummaryResponse:
        return cls(
            id=book.id,
            title=book.title,
            author=book.author,
            source_filename=book.source_filename,
            source_type=book.source_type,
            page_count=book.page_count,
            created_at=book.created_at,
        )


class ChapterSummaryResponse(BaseModel):
    id: int
    title: str
    sort_order: int
    chunk_count: int = 0

    @classmethod
    def from_chapter(cls, chapter: Chapter) -> ChapterSummaryResponse:
        chunk_count = len(chapter.text_chunks) if chapter.text_chunks else 0
        return cls(
            id=chapter.id,
            title=chapter.title,
            sort_order=chapter.sort_order,
            chunk_count=chunk_count,
        )


class BookDetailResponse(BookSummaryResponse):
    chapters: list[ChapterSummaryResponse] = []

    @classmethod
    def from_book(cls, book: Book) -> BookDetailResponse:
        return cls(
            id=book.id,
            title=book.title,
            author=book.author,
            source_filename=book.source_filename,
            source_type=book.source_type,
            page_count=book.page_count,
            created_at=book.created_at,
            chapters=[ChapterSummaryResponse.from_chapter(ch) for ch in book.chapters],
        )


class TextChunkResponse(BaseModel):
    chunk_index: int
    text: str

    @classmethod
    def from_chunk(cls, chunk: TextChunk) -> TextChunkResponse:
        return cls(chunk_index=chunk.chunk_index, text=chunk.text)


class ChapterDetailResponse(BaseModel):
    id: int
    book_id: int
    title: str
    sort_order: int
    chunks: list[TextChunkResponse] = []

    @classmethod
    def from_chapter(cls, chapter: Chapter) -> ChapterDetailResponse:
        return cls(
            id=chapter.id,
            book_id=chapter.book_id,
            title=chapter.title,
            sort_order=chapter.sort_order,
            chunks=[TextChunkResponse.from_chunk(c) for c in chapter.text_chunks],
        )
