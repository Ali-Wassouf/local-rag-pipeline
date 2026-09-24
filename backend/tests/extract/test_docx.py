from pathlib import Path

from app.extract import docx as docx_extractor

from .helpers import assert_valid_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_heading_styles_map_to_levels() -> None:
    blocks = docx_extractor.extract(FIXTURES / "headings.docx")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [h["level"] for h in headings] == [1, 2, 3]
    assert [h["text"] for h in headings] == [
        "Chapter One",
        "Section 1.1",
        "Subsection 1.1.1",
    ]


def test_normal_paragraphs_have_no_level() -> None:
    blocks = docx_extractor.extract(FIXTURES / "headings.docx")
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    assert len(paragraphs) == 3
    assert all(p["level"] is None for p in paragraphs)


def test_reading_order_preserved() -> None:
    blocks = docx_extractor.extract(FIXTURES / "headings.docx")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "heading", "paragraph", "heading", "paragraph"]


def test_table_becomes_table_block() -> None:
    blocks = docx_extractor.extract(FIXTURES / "table.docx")
    assert_valid_blocks(blocks)
    tables = [b for b in blocks if b["type"] == "table"]
    assert len(tables) == 1
    assert "Alpha" in tables[0]["text"]
    assert "|" in tables[0]["text"]


def test_list_becomes_list_block() -> None:
    blocks = docx_extractor.extract(FIXTURES / "list.docx")
    assert_valid_blocks(blocks)
    lists = [b for b in blocks if b["type"] == "list"]
    assert len(lists) == 1
    assert "Milk" in lists[0]["text"]
    assert "Eggs" in lists[0]["text"]
    assert "Bread" in lists[0]["text"]


def test_no_heading_styles_produces_zero_headings() -> None:
    blocks = docx_extractor.extract(FIXTURES / "no_headings.docx")
    assert_valid_blocks(blocks)
    assert all(b["type"] != "heading" for b in blocks)
    assert len(blocks) == 2


def test_blank_paragraphs_are_skipped() -> None:
    blocks = docx_extractor.extract(FIXTURES / "blank_paragraphs.docx")
    assert_valid_blocks(blocks)
    assert len(blocks) == 3
    assert [b["type"] for b in blocks] == ["heading", "paragraph", "paragraph"]


def test_anchor_is_sequential_block_index() -> None:
    blocks = docx_extractor.extract(FIXTURES / "headings.docx")
    assert [b["anchor"] for b in blocks] == list(range(len(blocks)))
