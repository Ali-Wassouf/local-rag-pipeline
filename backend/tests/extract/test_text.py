from pathlib import Path

from app.extract import text as text_extractor

from .helpers import assert_valid_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_plain_txt_has_no_headings() -> None:
    blocks = text_extractor.extract(FIXTURES / "plain.txt")
    assert_valid_blocks(blocks)
    assert all(b["type"] != "heading" for b in blocks)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "paragraph"
    assert blocks[1]["type"] == "paragraph"


def test_markdown_headings_map_to_levels() -> None:
    blocks = text_extractor.extract(FIXTURES / "headings.md")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [h["level"] for h in headings] == [1, 2, 3]
    assert [h["text"] for h in headings] == [
        "Chapter One",
        "Section 1.1",
        "Subsection 1.1.1",
    ]


def test_markdown_reading_order_preserved() -> None:
    blocks = text_extractor.extract(FIXTURES / "headings.md")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "heading", "paragraph", "heading", "paragraph"]


def test_markdown_table_becomes_table_block() -> None:
    blocks = text_extractor.extract(FIXTURES / "table.md")
    assert_valid_blocks(blocks)
    tables = [b for b in blocks if b["type"] == "table"]
    assert len(tables) == 1
    assert "Alpha" in tables[0]["text"]
    assert "|" in tables[0]["text"]


def test_markdown_list_becomes_list_block() -> None:
    blocks = text_extractor.extract(FIXTURES / "list.md")
    assert_valid_blocks(blocks)
    lists = [b for b in blocks if b["type"] == "list"]
    assert len(lists) == 1
    assert "Milk" in lists[0]["text"]
    assert "Eggs" in lists[0]["text"]
    assert "Bread" in lists[0]["text"]


def test_empty_file_returns_no_blocks() -> None:
    assert text_extractor.extract(FIXTURES / "empty.txt") == []


def test_whitespace_only_file_returns_no_blocks() -> None:
    assert text_extractor.extract(FIXTURES / "whitespace.txt") == []


def test_anchor_is_sequential_block_index() -> None:
    blocks = text_extractor.extract(FIXTURES / "headings.md")
    assert [b["anchor"] for b in blocks] == list(range(len(blocks)))
