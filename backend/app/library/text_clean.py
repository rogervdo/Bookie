from __future__ import annotations

import re

_SEPARATOR_CHARS = frozenset("-_=.*#~·•—–―│┃┄┅┆┇┊┋┈┉─━…·")
_MULTI_SPACE = re.compile(r"[ \t]+")
_HYPHEN_LINE_BREAK = re.compile(r"(\w)-\s*(?:-\s*)?\n\s*(\w)", re.MULTILINE)
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([:;,.!?])")
_SENTENCE_END = re.compile(r'[.!?]["\']?\s*$')
_BODY_START = re.compile(
    r"\b("
    r"Every|It is|It was|The outer|The inner|This|When|If|But|Neither|"
    r"One|Some|Many|Most|All|Each|Both|There|What|We |I |You |In the"
    r")\s",
    re.IGNORECASE,
)
_MIN_TITLE_PREFIX_LEN = 12


def is_separator_line(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 3:
        return False
    return all(c in _SEPARATOR_CHARS or c.isspace() for c in stripped)


def ends_sentence(line: str) -> bool:
    return bool(_SENTENCE_END.search(line.rstrip()))


def is_prose_continuation(previous: str, next_line: str) -> bool:
    if not next_line or not next_line[0].islower():
        return False
    if ends_sentence(previous):
        return False
    if "," in previous or len(previous) > 40:
        return True
    return bool(re.search(r"\w-\s*$", previous.rstrip()))


def is_metadata_line(line: str, next_line: str | None = None) -> bool:
    if ends_sentence(line):
        return False
    if next_line and is_prose_continuation(line, next_line):
        return False
    if "," in line and len(line) > 40:
        return False
    return not re.search(r"\w-\s*$", line.rstrip())


def fix_hyphenation(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = _HYPHEN_LINE_BREAK.sub(r"\1\2", text)
    return text


def _normalize_line(raw: str) -> str:
    line = _MULTI_SPACE.sub(" ", raw.strip())
    return _SPACE_BEFORE_PUNCT.sub(r"\1", line)


def _normalize_raw_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\f", "\n")


def _extract_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.split("\n"):
        if is_separator_line(raw):
            continue
        line = _normalize_line(raw)
        if line:
            lines.append(line)
    return lines


def _find_body_start(text: str) -> int | None:
    for match in _BODY_START.finditer(text):
        if match.start() >= _MIN_TITLE_PREFIX_LEN:
            return match.start()
    return None


def split_title_fragments(mashed: str) -> list[str]:
    text = mashed.strip()
    if not text:
        return []

    t = text
    t = re.sub(r"(Game)\s+(of\s+)", r"\1\n\2", t, count=1)
    t = re.sub(r"(\S)\s+(W\s+)", r"\1\n\2", t, count=1)
    t = re.sub(r"\s+(Jonathan\s+)", r"\n\1", t)
    t = re.sub(r"\s+(Thirty[- ]two\b)", r"\n\1", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+(London)\s*$", r"\n\1", t, flags=re.IGNORECASE)
    return [part.strip() for part in t.split("\n") if part.strip()]


def _split_mashed_line(line: str) -> tuple[list[str], list[str]]:
    """Split one PDF line that contains both imprint text and body prose."""
    start = _find_body_start(line)
    if start is None:
        if is_metadata_line(line):
            return split_title_fragments(line), []
        return [], [line]

    title = line[:start].strip()
    body = line[start:].strip()
    header = split_title_fragments(title) if title else []
    body_lines = [body] if body else []
    return header, body_lines


def _split_header_body(lines: list[str]) -> tuple[list[str], list[str]]:
    if not lines:
        return [], []

    if _find_body_start(lines[0]) is not None:
        header, body = _split_mashed_line(lines[0])
        return header, body + lines[1:]

    imprint: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        if not is_metadata_line(line, next_line):
            break
        imprint.append(line)
        index += 1

    return imprint, lines[index:]


def _should_join_lines(previous: str, nxt: str) -> bool:
    if ends_sentence(previous):
        return False
    if nxt and nxt[0].islower():
        return True
    return bool(re.search(r"[,;:\-]\s*$", previous.rstrip()))


def _reflow_body_lines(lines: list[str]) -> str:
    if not lines:
        return ""

    flow_lines = [_normalize_line(line) for line in "\n".join(lines).split("\n") if line.strip()]

    paragraphs: list[str] = []
    current = ""

    for line in flow_lines:
        if not current:
            current = line
            continue
        if _should_join_lines(current, line):
            current = f"{current.rstrip()} {line.lstrip()}"
        else:
            paragraphs.append(_MULTI_SPACE.sub(" ", current))
            current = line

    if current:
        paragraphs.append(_MULTI_SPACE.sub(" ", current))

    return "\n\n".join(paragraphs)


def clean_page_text(text: str) -> str:
    """Format PDF page text for TTS: imprint lines separated, body reflowed."""
    lines = _extract_lines(fix_hyphenation(_normalize_raw_text(text)))
    if not lines:
        return ""

    header_lines, body_lines = _split_header_body(lines)
    sections: list[str] = []

    if header_lines:
        sections.append("\n".join(header_lines))
    if body_lines:
        sections.append(_reflow_body_lines(body_lines))

    return "\n\n".join(sections)
