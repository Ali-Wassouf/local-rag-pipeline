from pathlib import Path

from app.extract import epub as epub_extractor

from .helpers import assert_valid_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_heading_tags_map_to_levels() -> None:
    blocks = epub_extractor.extract(FIXTURES / "headings.epub")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [h["level"] for h in headings] == [1, 2, 3]
    assert [h["text"] for h in headings] == [
        "Chapter One",
        "Section 1.1",
        "Subsection 1.1.1",
    ]


def test_normal_paragraphs_have_no_level() -> None:
    blocks = epub_extractor.extract(FIXTURES / "headings.epub")
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    assert len(paragraphs) == 3
    assert all(p["level"] is None for p in paragraphs)


def test_reading_order_preserved_across_chapter_files() -> None:
    # headings.epub spreads its three headings across two spine items
    # (chapter files) — this is the one thing genuinely specific to EPUB
    # versus the single-file formats: reading order and the block sequence
    # must survive crossing that file boundary.
    blocks = epub_extractor.extract(FIXTURES / "headings.epub")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "heading", "paragraph", "heading", "paragraph"]


def test_anchor_is_sequential_across_chapter_files() -> None:
    blocks = epub_extractor.extract(FIXTURES / "headings.epub")
    assert [b["anchor"] for b in blocks] == list(range(len(blocks)))


def test_table_becomes_table_block() -> None:
    blocks = epub_extractor.extract(FIXTURES / "table.epub")
    assert_valid_blocks(blocks)
    tables = [b for b in blocks if b["type"] == "table"]
    assert len(tables) == 1
    assert "Alpha" in tables[0]["text"]
    assert "|" in tables[0]["text"]


def test_list_becomes_list_block() -> None:
    blocks = epub_extractor.extract(FIXTURES / "list.epub")
    assert_valid_blocks(blocks)
    lists = [b for b in blocks if b["type"] == "list"]
    assert len(lists) == 1
    assert "Milk" in lists[0]["text"]
    assert "Eggs" in lists[0]["text"]
    assert "Bread" in lists[0]["text"]


def test_no_heading_tags_produces_zero_headings() -> None:
    blocks = epub_extractor.extract(FIXTURES / "no_headings.epub")
    assert_valid_blocks(blocks)
    assert all(b["type"] != "heading" for b in blocks)
    assert len(blocks) == 2


def test_blank_paragraphs_are_skipped() -> None:
    blocks = epub_extractor.extract(FIXTURES / "blank_paragraphs.epub")
    assert_valid_blocks(blocks)
    assert len(blocks) == 3
    assert [b["type"] for b in blocks] == ["heading", "paragraph", "paragraph"]


def test_navigation_document_is_not_extracted_as_content() -> None:
    # The EPUB3 nav document (book.spine's "nav" entry) is a list of links,
    # not book content — every fixture includes one, so if it leaked
    # through, every test above would already be failing on stray text;
    # this test names that guarantee explicitly rather than leaving it
    # implicit.
    blocks = epub_extractor.extract(FIXTURES / "headings.epub")
    texts = " ".join(b["text"] for b in blocks)
    assert "Chapter 1" not in texts  # the nav's link label, distinct from the "Chapter One" heading
