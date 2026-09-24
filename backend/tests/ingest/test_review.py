from app.ingest.review import estimate_chunks, find_uncovered_ranges, section_preview
from app.ingest.structure import SectionDraft

# --- section_preview -----------------------------------------------------


def test_preview_returns_full_text_when_shorter_than_max() -> None:
    section = SectionDraft(
        path="n1", title="T", display_path="T", depth=1, ordinal=1, char_start=0, char_end=5
    )
    assert section_preview("Hello", section, max_chars=100) == "Hello"


def test_preview_truncates_to_max_chars() -> None:
    raw_text = "Chapter One\n\n" + "x" * 500
    section = SectionDraft(
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=len(raw_text),
    )
    preview = section_preview(raw_text, section, max_chars=20)
    assert preview == raw_text[:20]
    assert len(preview) == 20


# --- estimate_chunks -------------------------------------------------------


def test_empty_text_estimates_zero_chunks() -> None:
    assert estimate_chunks("") == 0


def test_short_text_estimates_one_chunk() -> None:
    # ~4 chars/token heuristic: well under 700 tokens (2800 chars)
    assert estimate_chunks("word " * 100) == 1


def test_long_text_estimates_two_chunks() -> None:
    # 4000 chars / 4 chars-per-token ~= 1000 tokens: over the 700-token
    # first window, but within one more 600-token (700 - 100 overlap)
    # stride, so exactly 2 chunks.
    text = "a" * 4000
    assert estimate_chunks(text) == 2


# --- find_uncovered_ranges --------------------------------------------------


def test_no_gaps_when_sections_are_contiguous() -> None:
    sections = [
        SectionDraft(
            path="n1", title="A", display_path="A", depth=1, ordinal=1, char_start=0, char_end=10
        ),
        SectionDraft(
            path="n2", title="B", display_path="B", depth=1, ordinal=2, char_start=10, char_end=20
        ),
    ]
    assert find_uncovered_ranges(20, sections) == []


def test_no_sections_at_all_is_one_gap_spanning_everything() -> None:
    assert find_uncovered_ranges(20, []) == [(0, 20)]


def test_gap_between_two_sections_is_reported() -> None:
    sections = [
        SectionDraft(
            path="n1", title="A", display_path="A", depth=1, ordinal=1, char_start=0, char_end=10
        ),
        SectionDraft(
            path="n2", title="B", display_path="B", depth=1, ordinal=2, char_start=15, char_end=20
        ),
    ]
    assert find_uncovered_ranges(20, sections) == [(10, 15)]


def test_trailing_gap_after_last_section_is_reported() -> None:
    sections = [
        SectionDraft(
            path="n1", title="A", display_path="A", depth=1, ordinal=1, char_start=0, char_end=10
        ),
    ]
    assert find_uncovered_ranges(20, sections) == [(10, 20)]
