from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Book, Chapter, TextChunk
from app.library.pdf_extract import extract_pdf


async def import_pdf(
    session: AsyncSession,
    pdf_bytes: bytes,
    filename: str,
) -> Book:
    extracted = extract_pdf(pdf_bytes, filename)

    book = Book(
        title=extracted.title,
        author=extracted.author,
        source_filename=filename,
        source_type="pdf",
        page_count=extracted.page_count,
    )
    session.add(book)
    await session.flush()

    for page in extracted.pages:
        chapter = Chapter(
            book_id=book.id,
            title=f"Page {page.page_number}",
            sort_order=page.page_number - 1,
        )
        session.add(chapter)
        await session.flush()

        session.add(
            TextChunk(
                chapter_id=chapter.id,
                chunk_index=0,
                text=page.text,
            )
        )

    await session.commit()

    result = await session.execute(
        select(Book)
        .where(Book.id == book.id)
        .options(
            selectinload(Book.chapters).selectinload(Chapter.text_chunks),
        )
    )
    return result.scalar_one()


async def list_books(session: AsyncSession) -> list[Book]:
    result = await session.execute(select(Book).order_by(Book.created_at.desc()))
    return list(result.scalars().all())


async def get_book(session: AsyncSession, book_id: int) -> Book | None:
    result = await session.execute(
        select(Book)
        .where(Book.id == book_id)
        .options(
            selectinload(Book.chapters).selectinload(Chapter.text_chunks),
        )
    )
    return result.scalar_one_or_none()


async def get_chapter(session: AsyncSession, book_id: int, chapter_id: int) -> Chapter | None:
    result = await session.execute(
        select(Chapter)
        .where(Chapter.id == chapter_id, Chapter.book_id == book_id)
        .options(selectinload(Chapter.text_chunks))
    )
    return result.scalar_one_or_none()


async def delete_book(session: AsyncSession, book_id: int) -> bool:
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        return False
    await session.delete(book)
    await session.commit()
    return True


async def delete_chapter(session: AsyncSession, book_id: int, chapter_id: int) -> bool:
    chapter = await get_chapter(session, book_id, chapter_id)
    if chapter is None:
        return False
    await session.delete(chapter)
    await session.commit()
    return True
