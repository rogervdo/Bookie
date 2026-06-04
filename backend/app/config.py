import os
import ssl
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT / ".env")
DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "speaking.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"
DEFAULT_AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"
DEFAULT_SSL_CA_PATH = BACKEND_ROOT / "certs" / "ca.pem"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_audio_cache_dir() -> Path:
    raw = os.environ.get("AUDIO_CACHE_DIR")
    path = Path(raw) if raw else DEFAULT_AUDIO_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_ssl_ca_path(parsed_url=None) -> Path | None:
    """CA bundle for Aiven Postgres (DATABASE_SSL_CA, URL query, or certs/ca.pem)."""
    raw = os.environ.get("DATABASE_SSL_CA")
    if not raw and parsed_url is not None:
        raw = parsed_url.query.get("sslrootcert")
    if isinstance(raw, (list, tuple)):
        raw = raw[0] if raw else None

    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = BACKEND_ROOT / path
        return path if path.is_file() else None

    return DEFAULT_SSL_CA_PATH if DEFAULT_SSL_CA_PATH.is_file() else None


def get_sync_database_url(async_url: str | None = None) -> str:
    """Alembic uses a synchronous driver (psycopg2 understands sslrootcert in the URL)."""
    url = async_url or get_database_url()
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    if url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)

    if not url.startswith("postgresql"):
        return url

    parsed = make_url(url)
    ca_file = resolve_ssl_ca_path(parsed)
    if ca_file is None:
        return url

    parsed = parsed.difference_update_query(["sslmode", "sslrootcert"])
    parsed = parsed.update_query_dict(
        {
            "sslmode": "verify-full",
            "sslrootcert": str(ca_file.resolve()),
        }
    )
    return parsed.render_as_string(hide_password=False)


def is_sqlite(url: str | None = None) -> bool:
    return (url or get_database_url()).startswith("sqlite")


def _asyncpg_ssl_arg(sslmode: str | None, parsed_url) -> bool | ssl.SSLContext:
    """Map libpq sslmode values to asyncpg's ``ssl`` connect argument."""
    if sslmode == "disable":
        return False

    ca_file = resolve_ssl_ca_path(parsed_url)
    if ca_file:
        ctx = ssl.create_default_context()
        ctx.load_verify_locations(cafile=str(ca_file))
        if sslmode == "verify-ca":
            ctx.check_hostname = False
        return ctx

    if not sslmode or sslmode in ("prefer", "require"):
        return True

    ctx = ssl.create_default_context()
    if sslmode == "verify-ca":
        ctx.check_hostname = False
    return ctx


def get_async_engine_config(url: str | None = None) -> tuple[str, dict]:
    """URL and connect_args for SQLAlchemy create_async_engine.

    asyncpg does not accept libpq-style ``sslmode`` / ``sslrootcert`` query params;
    translate them to asyncpg's ``ssl`` argument. psycopg2 (Alembic) keeps them via
    :func:`get_sync_database_url`.
    """
    raw = url or get_database_url()
    if is_sqlite(raw):
        return raw, {"check_same_thread": False}

    if not raw.startswith("postgresql"):
        return raw, {}

    parsed = make_url(raw)
    sslmode = parsed.query.get("sslmode")
    if isinstance(sslmode, (list, tuple)):
        sslmode = sslmode[0] if sslmode else None

    strip = [key for key in ("sslmode", "sslrootcert") if key in parsed.query]
    if strip:
        parsed = parsed.difference_update_query(strip)

    clean_url = parsed.render_as_string(hide_password=False)

    connect_args: dict = {}
    if sslmode is not None or "sslmode" in raw:
        connect_args["ssl"] = _asyncpg_ssl_arg(sslmode, parsed)

    return clean_url, connect_args
