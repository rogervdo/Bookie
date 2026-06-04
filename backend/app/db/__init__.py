from app.config import DATA_DIR, get_database_url, is_sqlite
from app.db.base import Base
from app.db.models import AudioCacheEntry, Book, Chapter, ReadingProgress, TextChunk
from app.db.session import get_engine, get_session, get_session_factory, reset_engine


async def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


__all__ = [
    "AudioCacheEntry",
    "Base",
    "Book",
    "Chapter",
    "ReadingProgress",
    "TextChunk",
    "get_database_url",
    "get_engine",
    "get_session",
    "get_session_factory",
    "init_db",
    "is_sqlite",
    "reset_engine",
]
