"""Extractor for .pdf files (PyMuPDF).

Structure comes from the bookmark outline when the PDF has one; otherwise
a font-size heuristic looks for headings. `anchor` is the 1-indexed page
number — unlike the other formats, PDF pages are real and meaningful.
"""

from collections import Counter
from pathlib import Path
from typing import Any, Literal

import pymupdf

from app.extract.base import Block, ScannedDocumentError

# (text, max_font_size, kind) per page item, in reading order. Tables carry
# no meaningful font size — kept as 0.0 so the tuple shape stays uniform.
PageItem = tuple[str, float, Literal["text", "table"]]
PageBlocks = list[PageItem]

_HEADING_FONT_RATIO = 1.2  # a block's max font size must exceed body * this to read as a heading

# Fraction of pages a line must open/close to be treated as a repeating
# header/footer rather than real content. Not tuned against real documents
# yet — revisit once we have a query set (see docs/build-phases.md).
_HEADER_FOOTER_REPEAT_THRESHOLD = 0.6

# Whole-document average, not per-page: one scanned page in an otherwise
# real book must not trip this. Near-zero, not zero, to tolerate a mostly
# blank title/copyright page.
_SCANNED_CHARS_PER_PAGE_THRESHOLD = 10


def _guard_not_scanned(doc: pymupdf.Document) -> None:
    if len(doc) == 0:
        return
    total_chars = sum(len(doc[i].get_text().strip()) for i in range(len(doc)))
    average = total_chars / len(doc)
    if average < _SCANNED_CHARS_PER_PAGE_THRESHOLD:
        raise ScannedDocumentError(
            f"Average of {average:.1f} characters/page across {len(doc)} pages — "
            "this looks like a scanned PDF with no text layer. OCR is out of scope."
        )


def _page_text_items(page: pymupdf.Page) -> list[tuple[str, float, pymupdf.Rect]]:
    """(text, max_font_size, bbox) per text block on the page, in reading order."""
    page_dict = page.get_text("dict", sort=True)
    results: list[tuple[str, float, pymupdf.Rect]] = []
    for block in page_dict["blocks"]:
        if block.get("type") != 0:  # skip images etc.
            continue
        lines = []
        max_size = 0.0
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            line_text = "".join(span["text"] for span in spans).strip()
            if line_text:
                lines.append(line_text)
            for span in spans:
                max_size = max(max_size, span.get("size", 0.0))
        text = "\n".join(lines).strip()
        if text:
            results.append((text, max_size, pymupdf.Rect(block["bbox"])))
    return results


def _clean_row(cells: list[str | None]) -> list[str]:
    return [(c or "").strip() for c in cells]


def _table_to_markdown(rows: list[list[str | None]]) -> str:
    if not rows:
        return ""
    header, *body = rows
    header_cells = _clean_row(header)
    lines = [
        "| " + " | ".join(header_cells) + " |",
        "| " + " | ".join("---" for _ in header_cells) + " |",
    ]
    lines.extend("| " + " | ".join(_clean_row(row)) + " |" for row in body)
    return "\n".join(lines)


def _page_table_items(page: pymupdf.Page) -> list[tuple[str, pymupdf.Rect]]:
    results: list[tuple[str, pymupdf.Rect]] = []
    for table in page.find_tables().tables:
        markdown = _table_to_markdown(table.extract())
        if markdown:
            results.append((markdown, pymupdf.Rect(table.bbox)))
    return results


def _page_blocks(page: pymupdf.Page) -> PageBlocks:
    tables = _page_table_items(page)
    text_items = _page_text_items(page)

    def _inside_a_table(bbox: pymupdf.Rect) -> bool:
        return any(bbox.intersects(table_bbox) for _, table_bbox in tables)

    items: list[tuple[float, PageItem]] = []
    for text, size, bbox in text_items:
        if _inside_a_table(bbox):
            continue
        items.append((bbox.y0, (text, size, "text")))
    for markdown, bbox in tables:
        items.append((bbox.y0, (markdown, 0.0, "table")))

    items.sort(key=lambda item: item[0])
    return [item for _, item in items]


def _strip_headers_and_footers(pages: list[PageBlocks]) -> list[PageBlocks]:
    """Drop a page's first/last item when that same text opens/closes at
    least `_HEADER_FOOTER_REPEAT_THRESHOLD` of pages — a running header or
    footer, not real content."""
    if len(pages) < 2:
        return pages

    threshold_count = _HEADER_FOOTER_REPEAT_THRESHOLD * len(pages)
    first_line_counts = Counter(page[0][0] for page in pages if page)
    last_line_counts = Counter(page[-1][0] for page in pages if page)
    header_candidates = {t for t, c in first_line_counts.items() if c >= threshold_count}
    footer_candidates = {t for t, c in last_line_counts.items() if c >= threshold_count}

    stripped: list[PageBlocks] = []
    for page in pages:
        trimmed = list(page)
        if trimmed and trimmed[0][0] in header_candidates:
            trimmed = trimmed[1:]
        if trimmed and trimmed[-1][0] in footer_candidates:
            trimmed = trimmed[:-1]
        stripped.append(trimmed)
    return stripped


def _blocks_from_outline(pages: list[PageBlocks], toc: list[list[Any]]) -> list[Block]:
    headings_by_page: dict[int, list[tuple[int, str]]] = {}
    for level, title, page_num in toc:
        headings_by_page.setdefault(page_num, []).append((level, title))

    blocks: list[Block] = []
    for page_index, page in enumerate(pages):
        page_num = page_index + 1
        headings_here = headings_by_page.get(page_num, [])
        pending_titles = [title for _, title in headings_here]

        for level, title in headings_here:
            blocks.append(Block(type="heading", text=title, level=level, anchor=page_num))

        for text, _size, kind in page:
            if kind == "table":
                blocks.append(Block(type="table", text=text, level=None, anchor=page_num))
                continue
            if text in pending_titles:
                pending_titles.remove(text)
                continue
            blocks.append(Block(type="paragraph", text=text, level=None, anchor=page_num))

    return blocks


def _blocks_from_font_heuristic(pages: list[PageBlocks]) -> list[Block]:
    text_sizes = [size for page in pages for _text, size, kind in page if kind == "text"]
    # Body text is (almost) never smaller than headings, so the smallest size
    # in the document is a safe stand-in for the body baseline regardless of
    # how heading-heavy the document happens to be.
    heading_threshold = min(text_sizes) * _HEADING_FONT_RATIO if text_sizes else 0.0

    blocks: list[Block] = []
    for page_index, page in enumerate(pages):
        page_num = page_index + 1
        for text, size, kind in page:
            if kind == "table":
                blocks.append(Block(type="table", text=text, level=None, anchor=page_num))
            elif size > heading_threshold:
                blocks.append(Block(type="heading", text=text, level=1, anchor=page_num))
            else:
                blocks.append(Block(type="paragraph", text=text, level=None, anchor=page_num))
    return blocks


def extract(path: Path) -> list[Block]:
    doc = pymupdf.open(str(path))
    try:
        _guard_not_scanned(doc)
        raw_pages = [_page_blocks(doc[i]) for i in range(len(doc))]
        pages = _strip_headers_and_footers(raw_pages)
        toc = doc.get_toc()
        if toc:
            return _blocks_from_outline(pages, toc)
        return _blocks_from_font_heuristic(pages)
    finally:
        doc.close()
