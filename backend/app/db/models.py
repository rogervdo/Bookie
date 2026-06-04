from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[str | None] = mapped_column(String(512))
    source_filename: Mapped[str | None] = mapped_column(String(1024))
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="book", cascade="all, delete-orphan", order_by="Chapter.sort_order"
    )
    reading_progress: Mapped[ReadingProgress | None] = relationship(
        back_populates="book", cascade="all, delete-orphan", uselist=False
    )


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    book: Mapped[Book] = relationship(back_populates="chapters")
    text_chunks: Mapped[list[TextChunk]] = relationship(
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="TextChunk.chunk_index",
    )


class TextChunk(Base):
    __tablename__ = "text_chunks"
    __table_args__ = (
        UniqueConstraint("chapter_id", "chunk_index", name="uq_text_chunks_chapter_index"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    chapter: Mapped[Chapter] = relationship(back_populates="text_chunks")
    audio_cache_entries: Mapped[list[AudioCacheEntry]] = relationship(
        back_populates="text_chunk", cascade="all, delete-orphan"
    )


class ReadingProgress(Base):
    __tablename__ = "reading_progress"
    __table_args__ = (UniqueConstraint("book_id", name="uq_reading_progress_book"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chapter_id: Mapped[int] = mapped_column(
        ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[int | None] = mapped_column(ForeignKey("text_chunks.id", ondelete="SET NULL"))
    char_offset: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    voice: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    book: Mapped[Book] = relationship(back_populates="reading_progress")
    chapter: Mapped[Chapter] = relationship()
    chunk: Mapped[TextChunk | None] = relationship()


class AudioCacheEntry(Base):
    """Index for cached WAV files. Audio bytes live on disk or object storage — never in the DB."""

    __tablename__ = "audio_cache_index"
    __table_args__ = (
        UniqueConstraint("chunk_id", "voice", name="uq_audio_cache_chunk_voice"),
        Index("ix_audio_cache_object_key", "object_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("text_chunks.id", ondelete="CASCADE"), nullable=False
    )
    voice: Mapped[str] = mapped_column(String(64), nullable=False)
    cache_path: Mapped[str | None] = mapped_column(String(2048))
    object_key: Mapped[str | None] = mapped_column(String(1024))
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    text_chunk: Mapped[TextChunk] = relationship(back_populates="audio_cache_entries")
