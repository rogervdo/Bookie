from unittest.mock import patch

import pytest

from app.config import (
    get_async_engine_config,
    get_database_url,
    get_sync_database_url,
    is_sqlite,
)


@pytest.fixture(autouse=True)
def no_default_ca_file(monkeypatch, tmp_path):
    """Tests must not pick up a real backend/certs/ca.pem on disk."""
    missing = tmp_path / "missing-ca.pem"
    monkeypatch.setattr("app.config.DEFAULT_SSL_CA_PATH", missing)


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


def test_async_engine_translates_sslmode(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@host:5432/db?sslmode=require",
    )
    url, connect_args = get_async_engine_config()
    assert "sslmode" not in url
    assert connect_args["ssl"] is True
    sync = get_sync_database_url()
    assert "sslmode=require" in sync


def test_async_engine_verify_full_uses_ssl_context(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@host:5432/db?sslmode=verify-full",
    )
    _url, connect_args = get_async_engine_config()
    import ssl

    assert isinstance(connect_args["ssl"], ssl.SSLContext)


def test_async_engine_uses_ca_file_when_present(monkeypatch, tmp_path):
    import ssl

    ca_file = tmp_path / "ca.pem"
    ca_file.write_text("placeholder")
    monkeypatch.setenv("DATABASE_SSL_CA", str(ca_file))
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:pass@host.aivencloud.com:5432/defaultdb?sslmode=require",
    )

    with patch.object(ssl.SSLContext, "load_verify_locations"):
        _url, connect_args = get_async_engine_config()

    assert isinstance(connect_args["ssl"], ssl.SSLContext)
    sync = get_sync_database_url()
    assert "sslrootcert=" in sync
    assert "sslmode=verify-full" in sync
