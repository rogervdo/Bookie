from app.library.chunking import chunk_text, normalize_text


def test_normalize_text_collapses_whitespace():
    assert normalize_text("  hello   \n\n  world  ") == "hello\n\nworld"


def test_chunk_text_short_input():
    assert chunk_text("Short paragraph.") == ["Short paragraph."]


def test_chunk_text_splits_long_text():
    paragraph = "word " * 600
    chunks = chunk_text(paragraph.strip())
    assert len(chunks) >= 2
    assert all(len(c) <= 2000 for c in chunks)
    assert "".join(chunks).replace("\n\n", " ").count("word") >= 399
