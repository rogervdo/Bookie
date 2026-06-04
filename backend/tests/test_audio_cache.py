from pathlib import Path

import pytest

from app.db.models import AudioCacheEntry, Book, Chapter, TextChunk
from app.library import AudioCache


@pytest.mark.asyncio
async def test_audio_cache_writes_to_disk_not_db(db_session, tmp_path: Path):
    book = Book(title="Audio Book", source_type="pdf")
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Ch 1", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    chunk = TextChunk(chapter_id=chapter.id, chunk_index=0, text="Read this.")
    db_session.add(chunk)
    await db_session.commit()

    cache = AudioCache(cache_dir=tmp_path / "audio")
    wav = b"RIFFfake_wav_data"

    entry = await cache.write(db_session, chunk.id, "af_heart", wav)

    assert entry.cache_path is not None
    assert Path(entry.cache_path).read_bytes() == wav
    assert entry.file_size_bytes == len(wav)
    assert entry.object_key is None

    stored = await db_session.get(AudioCacheEntry, entry.id)
    assert stored is not None
    assert stored.cache_path == entry.cache_path


@pytest.mark.asyncio
async def test_audio_cache_read_and_delete(db_session, tmp_path: Path):
    book = Book(title="Cache IO", source_type="txt")
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Ch", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    chunk = TextChunk(chapter_id=chapter.id, chunk_index=0, text="Chunk.")
    db_session.add(chunk)
    await db_session.commit()

    cache = AudioCache(cache_dir=tmp_path / "audio")
    wav = b"RIFFtest"

    await cache.write(db_session, chunk.id, "af_bella", wav)
    assert await cache.read(db_session, chunk.id, "af_bella") == wav

    assert await cache.delete(db_session, chunk.id, "af_bella") is True
    assert await cache.read(db_session, chunk.id, "af_bella") is None


@pytest.mark.asyncio
async def test_audio_cache_object_key_for_cloud_backup(db_session, tmp_path: Path):
    book = Book(title="Cloud", source_type="pdf")
    db_session.add(book)
    await db_session.flush()

    chapter = Chapter(book_id=book.id, title="Ch", sort_order=0)
    db_session.add(chapter)
    await db_session.flush()

    chunk = TextChunk(chapter_id=chapter.id, chunk_index=0, text="Sync me.")
    db_session.add(chunk)
    await db_session.commit()

    cache = AudioCache(cache_dir=tmp_path / "audio")
    entry = await cache.write(
        db_session,
        chunk.id,
        "af_heart",
        b"RIFFcloud",
        object_key="speaking/audio/chunk_1_af_heart.wav",
    )

    assert entry.object_key == "speaking/audio/chunk_1_af_heart.wav"
    assert entry.cache_path is not None
