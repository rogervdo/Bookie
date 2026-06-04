from __future__ import annotations

import re

CHUNK_MIN = 500
CHUNK_MAX = 2000

_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [_WHITESPACE.sub(" ", p).strip() for p in text.split("\n")]
    return "\n\n".join(p for p in paragraphs if p)


def chunk_text(text: str, *, min_size: int = CHUNK_MIN, max_size: int = CHUNK_MAX) -> list[str]:
    """Split text into TTS-friendly chunks, preferring paragraph boundaries."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    if len(normalized) <= max_size:
        return [normalized]

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> None:
        nonlocal current, current_len
        if current:
            chunks.append("\n\n".join(current))
            current = []
            current_len = 0

    def append_paragraph(para: str) -> None:
        nonlocal current_len
        if current:
            current.append(para)
            current_len += 2 + len(para)
        else:
            current.append(para)
            current_len = len(para)

    for para in paragraphs:
        if len(para) > max_size:
            flush()
            chunks.extend(_split_long_paragraph(para, max_size=max_size))
            continue

        extra = (2 if current else 0) + len(para)
        if current and current_len + extra > max_size:
            flush()
        append_paragraph(para)
        if current_len >= min_size:
            flush()

    flush()
    return _merge_small_chunks(chunks, min_size=min_size, max_size=max_size)


def _split_long_paragraph(para: str, *, max_size: int) -> list[str]:
    parts: list[str] = []
    start = 0
    while start < len(para):
        end = min(start + max_size, len(para))
        if end < len(para):
            break_at = para.rfind(" ", start, end)
            if break_at > start:
                end = break_at
        piece = para[start:end].strip()
        if piece:
            parts.append(piece)
        start = end if end > start else end + 1
        while start < len(para) and para[start] == " ":
            start += 1
    return parts


def _merge_small_chunks(chunks: list[str], *, min_size: int, max_size: int) -> list[str]:
    if not chunks:
        return []
    merged: list[str] = []
    buffer = chunks[0]
    for piece in chunks[1:]:
        if len(buffer) < min_size and len(buffer) + 2 + len(piece) <= max_size:
            buffer = f"{buffer}\n\n{piece}"
        else:
            merged.append(buffer)
            buffer = piece
    merged.append(buffer)
    return merged
