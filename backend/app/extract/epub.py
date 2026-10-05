"""Extractor for .epub files (ebooklib + BeautifulSoup).

Reads each spine item's XHTML in reading order and walks its body: h1-h6
become heading blocks, p becomes a paragraph, ul/ol become a list block,
table serialises to Markdown — the same block-tag walk as docx.py, recursing
into wrapper tags (div, section, ...) but never descending into a tag once
it's been captured as a block, so nothing is double-counted. EPUB has no
native pagination, so `anchor` is a sequential index across the whole book,
continuing across chapter files rather than resetting per chapter. The
navigation document (EpubNav) is excluded — it's a list of links, not book
content.
"""

from collections.abc import Iterator
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag
from ebooklib import ITEM_DOCUMENT, epub

from app.extract.base import Block

_HEADING_LEVELS = {f"h{n}": n for n in range(1, 7)}
_BLOCK_TAGS = _HEADING_LEVELS.keys() | {"p", "ul", "ol", "table"}


def _iter_block_tags(node: Tag) -> Iterator[Tag]:
    for child in node.find_all(True, recursive=False):
        if child.name in _BLOCK_TAGS:
            yield child
        else:
            yield from _iter_block_tags(child)


def _table_to_markdown(table: Tag) -> str:
    rows = [
        [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        for row in table.find_all("tr")
    ]
    rows = [row for row in rows if row]
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
    book = epub.read_epub(str(path))
    blocks: list[Block] = []
    anchor = 0

    for idref, _linear in book.spine:
        item = book.get_item_with_id(idref)
        if item is None or item.get_type() != ITEM_DOCUMENT or isinstance(item, epub.EpubNav):
            continue

        soup = BeautifulSoup(item.get_content(), "html.parser")
        body = soup.body or soup

        for tag in _iter_block_tags(body):
            if tag.name in _HEADING_LEVELS:
                text = tag.get_text(strip=True)
                if text:
                    blocks.append(
                        Block(
                            type="heading",
                            text=text,
                            level=_HEADING_LEVELS[tag.name],
                            anchor=anchor,
                        )
                    )
                    anchor += 1
            elif tag.name == "p":
                text = tag.get_text(strip=True)
                if text:
                    blocks.append(Block(type="paragraph", text=text, level=None, anchor=anchor))
                    anchor += 1
            elif tag.name in ("ul", "ol"):
                items = [
                    item_text
                    for li in tag.find_all("li", recursive=False)
                    if (item_text := li.get_text(strip=True))
                ]
                if items:
                    text = "\n".join(f"- {i}" for i in items)
                    blocks.append(Block(type="list", text=text, level=None, anchor=anchor))
                    anchor += 1
            elif tag.name == "table":
                text = _table_to_markdown(tag)
                if text:
                    blocks.append(Block(type="table", text=text, level=None, anchor=anchor))
                    anchor += 1

    return blocks
