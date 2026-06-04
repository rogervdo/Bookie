from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_audio_cache_dir
from app.db.models import AudioCacheEntry


class AudioCache:
    """Local-disk WAV cache with optional object-storage key for cloud backup."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or get_audio_cache_dir()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, chunk_id: int, voice: str) -> Path:
        safe_voice = voice.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"chunk_{chunk_id}_{safe_voice}.wav"

    async def get_entry(
        self, session: AsyncSession, chunk_id: int, voice: str
    ) -> AudioCacheEntry | None:
        result = await session.execute(
            select(AudioCacheEntry).where(
                AudioCacheEntry.chunk_id == chunk_id,
                AudioCacheEntry.voice == voice,
            )
        )
        return result.scalar_one_or_none()

    async def read(
        self, session: AsyncSession, chunk_id: int, voice: str
    ) -> bytes | None:
        entry = await self.get_entry(session, chunk_id, voice)
        if entry is None or not entry.cache_path:
            return None
        path = Path(entry.cache_path)
        if not path.is_file():
            return None
        return path.read_bytes()

    async def write(
        self,
        session: AsyncSession,
        chunk_id: int,
        voice: str,
        wav_bytes: bytes,
        *,
        object_key: str | None = None,
    ) -> AudioCacheEntry:
        path = self.path_for(chunk_id, voice)
        path.write_bytes(wav_bytes)

        entry = await self.get_entry(session, chunk_id, voice)
        if entry is None:
            entry = AudioCacheEntry(
                chunk_id=chunk_id,
                voice=voice,
                cache_path=str(path),
                object_key=object_key,
                file_size_bytes=len(wav_bytes),
            )
            session.add(entry)
        else:
            entry.cache_path = str(path)
            entry.object_key = object_key
            entry.file_size_bytes = len(wav_bytes)

        await session.commit()
        await session.refresh(entry)
        return entry

    async def delete(
        self, session: AsyncSession, chunk_id: int, voice: str
    ) -> bool:
        entry = await self.get_entry(session, chunk_id, voice)
        if entry is None:
            return False
        if entry.cache_path:
            path = Path(entry.cache_path)
            if path.is_file():
                path.unlink()
        await session.delete(entry)
        await session.commit()
        return True
