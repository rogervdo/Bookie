import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Book, Chapter, ReadingProgress, TextChunk
from app.library import AudioCache


@pytest.mark.asyncio
async def test_book_chapter_chunk_hierarchy(db_session):
    book = Book(title="Test Book", author="Author", source_type="pdf", page_count=100)
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Chapter 1", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    chunk = TextChunk(chapter_id=chapter.id, chunk_index=0, text="Hello world.")
    db_session.add(chunk)
    await db_session.commit()

    result = await db_session.execute(
        select(Book)
        .where(Book.id == book.id)
        .options(selectinload(Book.chapters).selectinload(Chapter.text_chunks))
    )
    loaded = result.scalar_one()
    assert loaded.title == "Test Book"
    assert len(loaded.chapters) == 1
    assert loaded.chapters[0].text_chunks[0].text == "Hello world."


@pytest.mark.asyncio
async def test_reading_progress(db_session):
    book = Book(title="Progress Book", source_type="epub")
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Ch 1", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    chunk = TextChunk(chapter_id=chapter.id, chunk_index=0, text="Some text.")
    db_session.add(chunk)
    await db_session.flush()

    progress = ReadingProgress(
        book_id=book.id,
        chapter_id=chapter.id,
        chunk_id=chunk.id,
        char_offset=5,
        voice="af_heart",
    )
    db_session.add(progress)
    await db_session.commit()

    result = await db_session.execute(
        select(ReadingProgress).where(ReadingProgress.book_id == book.id)
    )
    loaded = result.scalar_one()
    assert loaded.voice == "af_heart"
    assert loaded.char_offset == 5


@pytest.mark.asyncio
async def test_text_chunk_unique_per_chapter(db_session):
    book = Book(title="Unique", source_type="txt")
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Ch", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    db_session.add(TextChunk(chapter_id=chapter.id, chunk_index=0, text="a"))
    db_session.add(TextChunk(chapter_id=chapter.id, chunk_index=0, text="b"))
    with pytest.raises(Exception):
        await db_session.commit()
