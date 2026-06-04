"""Regression tests using the real Inner Game sample PDF in backend/tests/."""

import pytest
from fastapi.testclient import TestClient

from app.library.pdf_extract import extract_pdf
from tests.conftest import inner_game_pdf_path
from tests.fixtures.inner_game import INNER_GAME_PAGE1_HEADER


def test_fixture_pdf_is_present():
    assert inner_game_pdf_path() is not None


def test_inner_game_extracts_three_pages(inner_game_pdf_bytes: bytes):
    book = extract_pdf(inner_game_pdf_bytes, "inner-game-fixture.pdf")
    assert book.page_count == 3
    assert len(book.pages) == 3
    assert book.pages[0].page_number == 1


def test_inner_game_page_one_golden_format(inner_game_pdf_bytes: bytes):
    p1 = extract_pdf(inner_game_pdf_bytes, "inner-game-fixture.pdf").pages[0].text
    header, sep, body = p1.partition("\n\n")

    assert header == INNER_GAME_PAGE1_HEADER
    assert sep == "\n\n"
    assert body.startswith("Every game is composed of two parts")
    assert "London Every" not in p1
    assert "The Inner Game of Tennis W Timothy" not in p1.replace(
        "The Inner Game\nof Tennis", ""
    )


def test_inner_game_page_one_title_and_body(inner_game_pdf_bytes: bytes):
    p1 = extract_pdf(inner_game_pdf_bytes, "inner-game-fixture.pdf").pages[0].text

    assert p1.startswith(INNER_GAME_PAGE1_HEADER)
    assert "\n\nEvery game is composed" in p1
    assert "outer game and an inner game." in p1


def test_inner_game_page_one_body_has_no_soft_wrap_breaks(inner_game_pdf_bytes: bytes):
    p1 = extract_pdf(inner_game_pdf_bytes, "inner-game-fixture.pdf").pages[0].text
    _, _, body = p1.partition("\n\nEvery game")
    assert body
    assert "\n" not in body.split(".")[0]


def test_inner_game_page_two_introduction(inner_game_pdf_bytes: bytes):
    p2 = extract_pdf(inner_game_pdf_bytes, "inner-game-fixture.pdf").pages[1].text
    assert "Introduction" in p2
    assert "tennisplayers" in p2


def test_inner_game_import_via_api(
    library_client: TestClient, inner_game_pdf_bytes: bytes
):
    response = library_client.post(
        "/api/library/import",
        files={
            "file": (
                "inner-game-fixture.pdf",
                inner_game_pdf_bytes,
                "application/pdf",
            )
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page_count"] == 3
    assert len(data["chapters"]) == 3
    assert all(ch["chunk_count"] == 1 for ch in data["chapters"])
    assert data["chapters"][0]["title"] == "Page 1"

    book_id = data["id"]
    chapter = library_client.get(
        f"/api/library/books/{book_id}/chapters/{data['chapters'][0]['id']}"
    ).json()
    text = chapter["chunks"][0]["text"]
    header, _, body = text.partition("\n\n")
    assert header == INNER_GAME_PAGE1_HEADER
    assert body.startswith("Every game is composed")
