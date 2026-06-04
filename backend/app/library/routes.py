from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.library import service
from app.schemas import BookDetailResponse, BookSummaryResponse, ChapterDetailResponse

router = APIRouter(prefix="/api/library", tags=["library"])


@router.post("/import", response_model=BookDetailResponse)
async def import_pdf(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> BookDetailResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Upload must be a .pdf file")

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Upload must be a PDF")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        book = await service.import_pdf(session, pdf_bytes, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BookDetailResponse.from_book(book)


@router.get("/books", response_model=list[BookSummaryResponse])
async def list_books(
    session: AsyncSession = Depends(get_session),
) -> list[BookSummaryResponse]:
    books = await service.list_books(session)
    return [BookSummaryResponse.from_book(book) for book in books]


@router.get("/books/{book_id}", response_model=BookDetailResponse)
async def get_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
) -> BookDetailResponse:
    book = await service.get_book(session, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookDetailResponse.from_book(book)


@router.get(
    "/books/{book_id}/chapters/{chapter_id}",
    response_model=ChapterDetailResponse,
)
async def get_chapter(
    book_id: int,
    chapter_id: int,
    session: AsyncSession = Depends(get_session),
) -> ChapterDetailResponse:
    chapter = await service.get_chapter(session, book_id, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return ChapterDetailResponse.from_chapter(chapter)


@router.delete("/books/{book_id}", status_code=204)
async def delete_book(
    book_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await service.delete_book(session, book_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Book not found")


@router.delete("/books/{book_id}/chapters/{chapter_id}", status_code=204)
async def delete_chapter(
    book_id: int,
    chapter_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    deleted = await service.delete_chapter(session, book_id, chapter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Page not found")
