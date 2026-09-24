from pathlib import Path

from app.extract import pptx as pptx_extractor

from .helpers import assert_valid_blocks

FIXTURES = Path(__file__).parent / "fixtures"


def test_slide_titles_become_headings() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "deck.pptx")
    assert_valid_blocks(blocks)
    headings = [b for b in blocks if b["type"] == "heading"]
    assert [h["text"] for h in headings] == ["Introduction", "Details"]
    assert all(h["level"] == 1 for h in headings)


def test_slide_body_becomes_paragraphs() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "deck.pptx")
    assert_valid_blocks(blocks)
    paragraphs = [b for b in blocks if b["type"] == "paragraph"]
    texts = [p["text"] for p in paragraphs]
    assert "Welcome to the deck." in texts
    assert "This slide sets the stage." in texts
    assert "Here are the details." in texts


def test_reading_order_is_slide_order_title_then_body() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "deck.pptx")
    types = [b["type"] for b in blocks]
    assert types == ["heading", "paragraph", "paragraph", "heading", "paragraph"]


def test_speaker_notes_included_after_slide_body() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "notes.pptx")
    assert_valid_blocks(blocks)
    texts = [b["text"] for b in blocks]
    assert texts == [
        "With Notes",
        "Body text on the slide.",
        "Remember to mention the roadmap here.",
    ]


def test_table_becomes_table_block() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "table.pptx")
    assert_valid_blocks(blocks)
    tables = [b for b in blocks if b["type"] == "table"]
    assert len(tables) == 1
    assert "Alpha" in tables[0]["text"]
    assert "|" in tables[0]["text"]


def test_blank_slide_produces_no_blocks() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "blank_slide.pptx")
    assert blocks == []


def test_anchor_is_sequential_block_index() -> None:
    blocks = pptx_extractor.extract(FIXTURES / "deck.pptx")
    assert [b["anchor"] for b in blocks] == list(range(len(blocks)))
