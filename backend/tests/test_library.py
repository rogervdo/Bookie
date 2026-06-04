import fitz
import pytest
from fastapi.testclient import TestClient


def make_sample_pdf(*, title: str = "Sample Book", body: str = "Hello from the test PDF.") -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), body)
    doc.set_metadata({"title": title, "author": "Test Author"})
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_import_list_and_fetch_book(library_client: TestClient):
    pdf_bytes = make_sample_pdf()

    response = library_client.post(
        "/api/library/import",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    imported = response.json()
    assert imported["title"] == "Sample Book"
    assert imported["author"] == "Test Author"
    assert imported["source_type"] == "pdf"
    assert len(imported["chapters"]) >= 1

    list_response = library_client.get("/api/library/books")
    assert list_response.status_code == 200
    books = list_response.json()
    assert len(books) == 1
    assert books[0]["title"] == "Sample Book"

    book_id = imported["id"]
    detail_response = library_client.get(f"/api/library/books/{book_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["chapters"][0]["chunk_count"] == 1

    chapter_id = imported["chapters"][0]["id"]
    chapter_response = library_client.get(
        f"/api/library/books/{book_id}/chapters/{chapter_id}"
    )
    assert chapter_response.status_code == 200
    chapter = chapter_response.json()
    assert len(chapter["chunks"]) == 1
    assert "Hello from the test PDF" in chapter["chunks"][0]["text"]


def test_import_one_chunk_per_page(library_client: TestClient):
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Page one text.")
    doc.new_page().insert_text((72, 72), "Page two text.")
    pdf_bytes = doc.tobytes()
    doc.close()

    response = library_client.post(
        "/api/library/import",
        files={"file": ("two.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["chapters"]) == 2
    assert all(ch["chunk_count"] == 1 for ch in data["chapters"])


def test_import_rejects_non_pdf(library_client: TestClient):
    response = library_client.post(
        "/api/library/import",
        files={"file": ("notes.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400


def test_get_missing_book_returns_404(library_client: TestClient):
    response = library_client.get("/api/library/books/999")
    assert response.status_code == 404


def test_delete_book(library_client: TestClient):
    pdf_bytes = make_sample_pdf()
    imported = library_client.post(
        "/api/library/import",
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    ).json()

    assert library_client.delete(f"/api/library/books/{imported['id']}").status_code == 204
    assert library_client.get("/api/library/books").json() == []
