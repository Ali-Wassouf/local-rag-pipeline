"""Extractor for .txt and .md files.

No page concept, so `anchor` is just a sequential block index. Markdown
syntax (`#` headings, `- ` lists, `| ... |` tables) is recognised when
present; plain .txt content with none of that syntax falls straight
through as paragraph blocks, letting the structure builder fall back to a
single root section.
"""

import re
from pathlib import Path

from app.extract.base import Block

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def extract(path: Path) -> list[Block]:
    lines = path.read_text(encoding="utf-8").split("\n")
    blocks: list[Block] = []
    anchor = 0
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal anchor
        text = "\n".join(paragraph_lines).strip()
        paragraph_lines.clear()
        if text:
            blocks.append(Block(type="paragraph", text=text, level=None, anchor=anchor))
            anchor += 1

    index = 0
    total = len(lines)
    while index < total:
        line = lines[index]

        if not line.strip():
            flush_paragraph()
            index += 1
            continue

        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            heading_text = heading_match.group(2).strip()
            if heading_text:
                level = len(heading_match.group(1))
                blocks.append(
                    Block(type="heading", text=heading_text, level=level, anchor=anchor)
                )
                anchor += 1
            index += 1
            continue

        if _TABLE_ROW_RE.match(line):
            flush_paragraph()
            table_lines = []
            while index < total and _TABLE_ROW_RE.match(lines[index]):
                table_lines.append(lines[index])
                index += 1
            blocks.append(
                Block(type="table", text="\n".join(table_lines).strip(), level=None, anchor=anchor)
            )
            anchor += 1
            continue

        if _LIST_ITEM_RE.match(line):
            flush_paragraph()
            list_lines = []
            while index < total and _LIST_ITEM_RE.match(lines[index]):
                list_lines.append(lines[index])
                index += 1
            blocks.append(
                Block(type="list", text="\n".join(list_lines).strip(), level=None, anchor=anchor)
            )
            anchor += 1
            continue

        paragraph_lines.append(line)
        index += 1

    flush_paragraph()
    return blocks
