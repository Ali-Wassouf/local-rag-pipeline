from app.ingest.chunk import _tokenizer, chunk_section


def _text_with_exact_token_count(unit: str, target_tokens: int) -> str:
    """Builds text with exactly `target_tokens` tokens, verified against the
    real tokenizer rather than assumed."""
    tokenizer = _tokenizer()
    text = unit * (target_tokens + 20)
    encoding = tokenizer.encode(text, add_special_tokens=False)
    assert len(encoding.ids) >= target_tokens
    end_char = encoding.offsets[target_tokens - 1][1]
    return text[:end_char]


def test_short_section_is_a_single_chunk() -> None:
    text = _text_with_exact_token_count("banana ", 50)
    chunks = chunk_section("Ch. 1 > Fruit", text, section_char_offset=0)
    assert len(chunks) == 1
    assert chunks[0].token_count == 50
    assert chunks[0].text == text
    assert chunks[0].char_start == 0
    assert chunks[0].char_end == len(text)


def test_section_sized_for_two_windows() -> None:
    text = _text_with_exact_token_count("banana ", 1000)
    chunks = chunk_section("Ch. 1 > Fruit", text, section_char_offset=0)
    assert len(chunks) == 2
    assert chunks[0].token_count == 700
    assert chunks[1].token_count == 400  # 1000 - 600 stride
    # the 100-token overlap must show up as a character-level overlap
    assert chunks[1].char_start < chunks[0].char_end


def test_tiny_section_does_not_crash() -> None:
    chunks = chunk_section("Ch. 1", "Hi.", section_char_offset=0)
    assert len(chunks) == 1
    assert chunks[0].token_count >= 1


def test_chunk_offsets_are_relative_to_the_document() -> None:
    text = _text_with_exact_token_count("banana ", 50)
    chunks = chunk_section("Ch. 1", text, section_char_offset=1000)
    assert chunks[0].char_start == 1000
    assert chunks[0].char_end == 1000 + len(text)


def test_embed_text_starts_with_breadcrumb_text_does_not() -> None:
    text = "Some analysis of storage engines."
    chunks = chunk_section("Chapter One > Section 1.1", text, section_char_offset=0)
    chunk = chunks[0]
    assert chunk.embed_text == f"Chapter One > Section 1.1\n\n{text}"
    assert chunk.text == text
    assert not chunk.text.startswith("Chapter One")


def test_ordinal_is_sequential_and_one_indexed() -> None:
    text = _text_with_exact_token_count("banana ", 1000)
    chunks = chunk_section("Ch. 1", text, section_char_offset=0)
    assert [c.ordinal for c in chunks] == [1, 2]


def test_chunks_never_exceed_their_sections_char_range() -> None:
    section_a_text = _text_with_exact_token_count("apple ", 900)
    section_b_text = _text_with_exact_token_count("orange ", 900)

    a_chunks = chunk_section("Section A", section_a_text, section_char_offset=0)
    b_offset = len(section_a_text)
    b_chunks = chunk_section("Section B", section_b_text, section_char_offset=b_offset)

    for chunk in a_chunks:
        assert 0 <= chunk.char_start
        assert chunk.char_end <= len(section_a_text)

    for chunk in b_chunks:
        assert b_offset <= chunk.char_start
        assert chunk.char_end <= b_offset + len(section_b_text)
