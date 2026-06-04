import pytest

from app.config import get_database_url, get_sync_database_url, is_sqlite


def test_default_database_url_is_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    url = get_database_url()
    assert url.startswith("sqlite+aiosqlite")
    assert is_sqlite(url)


def test_postgres_url_detection(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@host:5432/db",
    )
    url = get_database_url()
    assert not is_sqlite(url)
    sync = get_sync_database_url(url)
    assert sync.startswith("postgresql+psycopg2")
