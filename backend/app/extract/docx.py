"""Extractor for .docx files (python-docx).

Heading N styles map to heading blocks; List Bullet/List Number paragraphs
are grouped into list blocks; tables are serialised to Markdown. DOCX has
no native pagination, so `anchor` is a sequential block index.
"""

import re
from collections.abc import Iterator
from pathlib import Path

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from app.extract.base import Block

_HEADING_STYLE_RE = re.compile(r"^Heading (\d+)$")
_LIST_STYLE_PREFIXES = ("List Bullet", "List Number")


def _iter_block_items(document: DocxDocument) -> Iterator[DocxParagraph | DocxTable]:
    for child in document.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield DocxParagraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield DocxTable(child, document)


def _table_to_markdown(table: DocxTable) -> str:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not rows:
        return ""
    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)


def extract(path: Path) -> list[Block]:
    document = Document(str(path))
    blocks: list[Block] = []
    anchor = 0
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal anchor
        if list_items:
            text = "\n".join(f"- {item}" for item in list_items)
            blocks.append(Block(type="list", text=text, level=None, anchor=anchor))
            anchor += 1
            list_items.clear()

    for item in _iter_block_items(document):
        if isinstance(item, DocxTable):
            flush_list()
            table_text = _table_to_markdown(item)
            if table_text:
                blocks.append(Block(type="table", text=table_text, level=None, anchor=anchor))
                anchor += 1
            continue

        text = item.text.strip()
        if not text:
            continue

        style_name = item.style.name or "" if item.style is not None else ""

        heading_match = _HEADING_STYLE_RE.match(style_name)
        if heading_match:
            flush_list()
            level = int(heading_match.group(1))
            if 1 <= level <= 6:
                blocks.append(Block(type="heading", text=text, level=level, anchor=anchor))
                anchor += 1
            continue

        if style_name.startswith(_LIST_STYLE_PREFIXES):
            list_items.append(text)
            continue

        flush_list()
        blocks.append(Block(type="paragraph", text=text, level=None, anchor=anchor))
        anchor += 1

    flush_list()
    return blocks
