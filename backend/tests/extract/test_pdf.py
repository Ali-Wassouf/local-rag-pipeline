from pathlib import Path

import pytest

from app.extract import pdf as pdf_extractor
from app.extract.base import ScannedDocumentError

from .helpers import assert_valid_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_outline_produces_heading_blocks_matching_toc() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "outline.pdf")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [(h["level"], h["text"]) for h in headings] == [
        (1, "Chapter One"),
        (2, "Section 1.1"),
        (2, "Section 1.2"),
    ]


def test_outline_body_text_becomes_paragraphs() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "outline.pdf")
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    texts = [p["text"] for p in paragraphs]
    assert "This is the introduction paragraph before any subsection." in texts
    assert "Body text for section 1.1." in texts
    assert "Body text for section 1.2." in texts


def test_outline_reading_order_heading_then_body_per_page() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "outline.pdf")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "heading", "paragraph", "heading", "paragraph"]


def test_anchor_equals_one_indexed_page_number() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "outline.pdf")
    assert [b["anchor"] for b in blocks] == [1, 1, 2, 2, 3, 3]


def test_corrupted_file_raises_clear_exception() -> None:
    with pytest.raises(Exception):
        pdf_extractor.extract(FIXTURES / "corrupted.pdf")


def test_no_outline_and_no_font_signal_produces_zero_headings() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "no_outline_no_heuristic.pdf")
    assert_valid_blocks(blocks)
    assert all(b["type"] != "heading" for b in blocks)
    assert len(blocks) == 3


def test_no_outline_but_clear_font_jump_is_detected_as_heading() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "no_outline_with_heuristic.pdf")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [h["text"] for h in headings] == ["Big Heading One", "Big Heading Two"]


def test_font_heuristic_reading_order_preserved() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "no_outline_with_heuristic.pdf")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "heading", "paragraph"]


def test_repeating_header_and_footer_are_stripped() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "headers_footers.pdf")
    texts = [b["text"] for b in blocks]
    assert "My Book Title" not in texts
    assert "Confidential Draft" not in texts


def test_line_repeating_on_only_two_of_five_pages_is_not_stripped() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "headers_footers.pdf")
    texts = [b["text"] for b in blocks]
    assert texts.count("See appendix B for details.") == 2


def test_unique_body_text_survives_header_footer_stripping() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "headers_footers.pdf")
    texts = [b["text"] for b in blocks]
    assert "Chapter openings often begin with a short overview sentence." in texts
    assert "The middle chapters cover the bulk of the material." in texts
    assert "The final chapter wraps up the discussion." in texts


def test_table_becomes_table_block() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "table.pdf")
    assert_valid_blocks(blocks)
    tables = [b for b in blocks if b["type"] == "table"]
    assert len(tables) == 1
    assert "Alpha" in tables[0]["text"]
    assert "|" in tables[0]["text"]


def test_table_cells_are_not_duplicated_as_paragraphs() -> None:
    blocks = pdf_extractor.extract(FIXTURES / "table.pdf")
    paragraphs = [b["text"] for b in blocks if b["type"] == "paragraph"]
    assert "Alpha" not in paragraphs
    assert "1" not in paragraphs


def test_scanned_pdf_raises_scanned_document_error() -> None:
    with pytest.raises(ScannedDocumentError):
        pdf_extractor.extract(FIXTURES / "scanned.pdf")


def test_document_average_not_per_page_drives_the_guard() -> None:
    # One scanned page among four real text pages must not false-positive —
    # the guard looks at the whole-document average, not any single page.
    blocks = pdf_extractor.extract(FIXTURES / "mostly_text_one_scanned_page.pdf")
    assert_valid_blocks(blocks)
    assert len(blocks) == 4
