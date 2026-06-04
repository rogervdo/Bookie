from app.library.text_clean import clean_page_text, ends_sentence, is_metadata_line, is_separator_line


def test_is_separator_line():
    assert is_separator_line("------------------------------")
    assert is_separator_line("========")
    assert not is_separator_line("Chapter 1")
    assert not is_separator_line("-- note")


def test_ends_sentence():
    assert ends_sentence("Hello world.")
    assert ends_sentence('He said "stop."')
    assert not ends_sentence("The Inner Game of Tennis")
    assert not ends_sentence("W Timothy Gallwey")


def test_is_metadata_line():
    assert is_metadata_line("The Inner Game of Tennis")
    assert is_metadata_line("W Timothy Gallwey")
    assert not is_metadata_line(
        "Every game is composed of two parts, an outer game and an inner"
    )
    assert not is_metadata_line("game.", "It is the thesis")


def test_clean_page_text_removes_rules():
    raw = "Introduction\n\n--------------------\n\nHello world."
    assert "----" not in clean_page_text(raw)
    assert "Hello world." in clean_page_text(raw)


def test_title_block_keeps_line_breaks():
    raw = (
        "The Inner Game\n"
        "of Tennis\n"
        "W Timothy Gallwey\n"
        "Jonathan Cape\n"
        "Thirty-two Bedford Square London"
    )
    cleaned = clean_page_text(raw)
    assert "The Inner Game\nof Tennis" in cleaned
    assert "W Timothy Gallwey" in cleaned
    assert "Jonathan Cape" in cleaned
    assert "The Inner Game of Tennis\n\nW" not in cleaned.replace(
        "The Inner Game\nof Tennis", ""
    )


def test_title_then_body_on_same_page():
    raw = (
        "The Inner Game\n"
        "of Tennis\n"
        "W Timothy Gallwey\n"
        "Every game is composed of two parts, an outer game and an inner\n"
        "game."
    )
    cleaned = clean_page_text(raw)
    assert "The Inner Game\nof Tennis" in cleaned
    assert "inner game." in cleaned
    assert "inner\n" not in cleaned


def test_mashed_title_block_before_body():
    raw = (
        "The Inner Game of Tennis W Timothy Gallwey Jonathan Cape "
        "Thirty-two Bedford Square London "
        "Every game is composed of two parts, an outer game and an inner game."
    )
    cleaned = clean_page_text(raw)
    assert "Jonathan Cape" in cleaned
    assert "Every game is composed" in cleaned
    assert "London Every" not in cleaned
    assert "\n" in cleaned.split("Every game")[0]


def test_body_joins_soft_wraps():
    raw = (
        "Every game is composed of two parts, an outer game and an inner\n"
        "game. It is the thesis of this book that neither mastery nor satisfaction\n"
        "can be found in the playing of any game."
    )
    cleaned = clean_page_text(raw)
    assert "inner game." in cleaned
    assert "satisfaction can" in cleaned
    assert "\ncan" not in cleaned


def test_hyphenation_joined():
    raw = "giving some atten-\ntion to the inner game."
    assert "attention" in clean_page_text(raw)
    assert "atten-\n" not in clean_page_text(raw)


def test_hyphenation_double_dash():
    raw = "Mas- -\ntering the inner game"
    assert "Mastering" in clean_page_text(raw)
