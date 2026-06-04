import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_ROOT / ".env")
DATA_DIR = BACKEND_ROOT / "data"
DEFAULT_SQLITE_PATH = DATA_DIR / "speaking.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_SQLITE_PATH}"
DEFAULT_AUDIO_CACHE_DIR = DATA_DIR / "audio_cache"


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_audio_cache_dir() -> Path:
    raw = os.environ.get("AUDIO_CACHE_DIR")
    path = Path(raw) if raw else DEFAULT_AUDIO_CACHE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_sync_database_url(async_url: str | None = None) -> str:
    """Alembic uses a synchronous driver."""
    url = async_url or get_database_url()
    if url.startswith("sqlite+aiosqlite"):
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    if url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
    return url


def is_sqlite(url: str | None = None) -> bool:
    return (url or get_database_url()).startswith("sqlite")
