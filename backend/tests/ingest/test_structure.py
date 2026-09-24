from pathlib import Path

from app.extract import docx as docx_extractor
from app.extract import pdf as pdf_extractor
from app.extract import pptx as pptx_extractor
from app.extract import text as text_extractor
from app.extract.base import Block
from app.ingest.structure import build_structure

EXTRACT_FIXTURES = Path(__file__).parent.parent / "extract" / "fixtures"


def _heading(text: str, level: int) -> Block:
    return Block(type="heading", text=text, level=level, anchor=0)


def _para(text: str) -> Block:
    return Block(type="paragraph", text=text, level=None, anchor=0)


def _table(text: str) -> Block:
    return Block(type="table", text=text, level=None, anchor=0)


def _assert_contiguous_and_round_trips(raw_text: str, sections: list) -> None:
    assert sections, "expected at least one section"
    assert sections[0].char_start == 0
    for a, b in zip(sections, sections[1:]):
        assert a.char_end == b.char_start, "gap or overlap between adjacent sections"
    assert sections[-1].char_end == len(raw_text)
    reconstructed = "".join(raw_text[s.char_start : s.char_end] for s in sections)
    assert reconstructed == raw_text


# --- tree shape -------------------------------------------------------


def test_three_sibling_headings_no_nesting() -> None:
    blocks = [
        _heading("Chapter One", 1),
        _para("Body one."),
        _heading("Chapter Two", 1),
        _para("Body two."),
        _heading("Chapter Three", 1),
        _para("Body three."),
    ]
    result = build_structure(blocks)
    assert [s.title for s in result.sections] == ["Chapter One", "Chapter Two", "Chapter Three"]
    assert [s.path for s in result.sections] == ["n1", "n2", "n3"]
    assert all(s.depth == 1 for s in result.sections)
    assert [s.ordinal for s in result.sections] == [1, 2, 3]


def test_nested_headings_produce_correct_path_and_depth() -> None:
    blocks = [
        _heading("Chapter One", 1),
        _heading("Section 1.1", 2),
        _heading("Subsection 1.1.1", 3),
        _para("Deepest body text."),
    ]
    result = build_structure(blocks)
    assert [s.title for s in result.sections] == [
        "Chapter One",
        "Section 1.1",
        "Subsection 1.1.1",
    ]
    assert [s.path for s in result.sections] == ["n1", "n1.n1", "n1.n1.n1"]
    assert [s.depth for s in result.sections] == [1, 2, 3]


def test_level_skip_nests_under_nearest_lower_level() -> None:
    blocks = [
        _heading("Chapter One", 1),
        _heading("Deep Subsection", 3),  # no level-2 heading in between
        _para("Body."),
    ]
    result = build_structure(blocks)
    assert [s.title for s in result.sections] == ["Chapter One", "Deep Subsection"]
    assert [s.path for s in result.sections] == ["n1", "n1.n1"]
    assert [s.depth for s in result.sections] == [1, 2]


def test_display_path_joins_ancestor_titles() -> None:
    blocks = [
        _heading("Chapter One", 1),
        _heading("Section 1.1", 2),
    ]
    result = build_structure(blocks)
    assert result.sections[0].display_path == "Chapter One"
    assert result.sections[1].display_path == "Chapter One > Section 1.1"


# --- fallback / preamble handling --------------------------------------


def test_no_headings_produces_single_root_section() -> None:
    blocks = [_para("Just some plain text."), _para("More plain text.")]
    result = build_structure(blocks, document_title="My Document")
    assert len(result.sections) == 1
    section = result.sections[0]
    assert section.title == "My Document"
    assert section.path == "n1"
    assert section.depth == 1
    assert section.source == "detected"
    assert section.char_start == 0
    assert section.char_end == len(result.raw_text)


def test_no_headings_and_no_document_title_falls_back_to_untitled() -> None:
    result = build_structure([_para("Text with no title given.")])
    assert result.sections[0].title == "Untitled"


def test_leading_text_before_first_heading_becomes_preface() -> None:
    blocks = [
        _para("This intro comes before any heading."),
        _heading("Chapter One", 1),
        _para("Body one."),
    ]
    result = build_structure(blocks)
    assert result.sections[0].title == "Preface"
    assert result.sections[0].path == "n1"
    assert result.sections[1].title == "Chapter One"
    assert result.sections[1].path == "n2"


def test_no_leading_text_means_no_preface_section() -> None:
    blocks = [_heading("Chapter One", 1), _para("Body one.")]
    result = build_structure(blocks)
    assert [s.title for s in result.sections] == ["Chapter One"]


def test_empty_blocks_list_produces_single_empty_root_section() -> None:
    result = build_structure([], document_title="Empty Doc")
    assert result.raw_text == ""
    assert len(result.sections) == 1
    section = result.sections[0]
    assert section.title == "Empty Doc"
    assert section.char_start == 0
    assert section.char_end == 0


# --- content attachment -------------------------------------------------


def test_heading_immediately_followed_by_heading_has_minimal_char_range() -> None:
    blocks = [_heading("Chapter One", 1), _heading("Chapter Two", 1), _para("Body two.")]
    result = build_structure(blocks)
    chapter_one = result.sections[0]
    # No body of its own — its range covers only its own heading text (plus
    # any absorbed separator), nothing from Chapter Two.
    assert result.raw_text[chapter_one.char_start : chapter_one.char_end].strip() == "Chapter One"


def test_table_block_after_heading_attaches_to_that_section() -> None:
    blocks = [
        _heading("Chapter One", 1),
        _table("| A | B |\n| --- | --- |\n| 1 | 2 |"),
        _heading("Chapter Two", 1),
    ]
    result = build_structure(blocks)
    chapter_one_text = result.raw_text[
        result.sections[0].char_start : result.sections[0].char_end
    ]
    assert "| A | B |" in chapter_one_text


# --- coverage / round-trip property tests -------------------------------


def test_coverage_is_contiguous_with_no_gaps_or_overlaps() -> None:
    blocks = [
        _para("Leading preface text."),
        _heading("Chapter One", 1),
        _para("Body one."),
        _heading("Section 1.1", 2),
        _para("Nested body."),
        _heading("Chapter Two", 1),
        _para("Body two."),
    ]
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)


def test_coverage_holds_with_no_headings_at_all() -> None:
    blocks = [_para("Only plain text."), _para("More plain text.")]
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)


def test_coverage_holds_for_empty_blocks() -> None:
    result = build_structure([])
    assert result.sections[0].char_start == result.sections[0].char_end == 0


# --- integration against real extractor output ---------------------------


def test_coverage_holds_for_real_markdown_extraction() -> None:
    blocks = text_extractor.extract(EXTRACT_FIXTURES / "headings.md")
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)


def test_coverage_holds_for_real_docx_extraction() -> None:
    blocks = docx_extractor.extract(EXTRACT_FIXTURES / "headings.docx")
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)


def test_coverage_holds_for_real_pptx_extraction() -> None:
    blocks = pptx_extractor.extract(EXTRACT_FIXTURES / "deck.pptx")
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)


def test_coverage_holds_for_real_pdf_extraction() -> None:
    blocks = pdf_extractor.extract(EXTRACT_FIXTURES / "outline.pdf")
    result = build_structure(blocks)
    _assert_contiguous_and_round_trips(result.raw_text, result.sections)
