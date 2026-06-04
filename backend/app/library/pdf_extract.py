from __future__ import annotations

from dataclasses import dataclass, field

import fitz

from app.library.text_clean import clean_page_text


@dataclass
class ExtractedPage:
    page_number: int
    text: str


@dataclass
class ExtractedBook:
    title: str
    author: str | None
    page_count: int
    pages: list[ExtractedPage] = field(default_factory=list)


def extract_pdf(pdf_bytes: bytes, filename: str) -> ExtractedBook:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Invalid PDF: {exc}") from exc

    try:
        meta = doc.metadata or {}
        title = (meta.get("title") or "").strip() or _title_from_filename(filename)
        author = (meta.get("author") or "").strip() or None
        page_count = doc.page_count

        pages = _pages_from_document(doc)
        if not pages:
            raise ValueError("PDF contains no extractable text")

        return ExtractedBook(
            title=title,
            author=author,
            page_count=page_count,
            pages=pages,
        )
    finally:
        doc.close()


def _title_from_filename(filename: str) -> str:
    name = filename.rsplit("/", 1)[-1]
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    return name.replace("_", " ").strip() or "Untitled"


def _pages_from_document(doc: fitz.Document) -> list[ExtractedPage]:
    pages: list[ExtractedPage] = []
    for page_index in range(doc.page_count):
        raw = doc.load_page(page_index).get_text("text")
        text = clean_page_text(raw)
        if text:
            pages.append(
                ExtractedPage(
                    page_number=page_index + 1,
                    text=text,
                )
            )
    return pages
