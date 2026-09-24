"""Fold a document's `Block` list into `sections` rows.

Design notes (see conversation / commit history for the full reasoning):

- `raw_text` is *built from the blocks* (joined with a separator), not the
  original file bytes — PDF/DOCX/PPTX have no coherent "original text
  stream" once tables are serialised to Markdown and headers/footers are
  stripped, and a heading's block text ("Chapter One") already differs from
  whatever the source markup looked like ("# Chapter One"). Building
  `raw_text` from the same blocks whose offsets we're computing makes every
  offset exact by construction instead of a fragile substring search.

- ltree `path` labels are positional (`n1`, `n1.n2`, ...), never derived
  from the title: titles carry arbitrary characters ltree can't hold, two
  siblings can share a title, and a title edit (review screen) must never
  require rewriting a whole subtree's paths. `title`/`display_path` already
  carry the human-readable form.

- Sections are a strict, non-overlapping partition of `raw_text`. A
  section with children owns only the text between its own heading and the
  next heading of any level — never its descendants' text — otherwise
  chunking per section (see CLAUDE.md invariant 2) would double-count.

- A heading level skip (H1 -> H3, no H2) nests the H3 under the H1: a new
  heading's parent is the nearest still-open heading with a strictly lower
  level, not a level exactly one less.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.extract.base import Block
from app.models.document import Document
from app.models.section import Section, StructureSource

_SEPARATOR = "\n\n"
_DEFAULT_TITLE = "Untitled"


@dataclass
class SectionDraft:
    path: str
    title: str
    display_path: str
    depth: int
    ordinal: int
    char_start: int
    char_end: int
    source: Literal["detected", "manual"] = "detected"


@dataclass
class StructureResult:
    raw_text: str
    sections: list[SectionDraft]


@dataclass
class _OpenHeading:
    level: int
    draft: SectionDraft
    next_child_ordinal: int = 1


def _raw_text_and_offsets(blocks: list[Block]) -> tuple[str, list[tuple[int, int]]]:
    """Join block texts with `_SEPARATOR`, returning the joined string and
    each block's exact (start, end) offset into it."""
    parts: list[str] = []
    offsets: list[tuple[int, int]] = []
    cursor = 0
    last_index = len(blocks) - 1
    for i, block in enumerate(blocks):
        text = block["text"]
        start = cursor
        cursor = start + len(text)
        offsets.append((start, cursor))
        parts.append(text)
        if i != last_index:
            cursor += len(_SEPARATOR)
    return _SEPARATOR.join(parts), offsets


def _close_gaps(sections: list[SectionDraft], raw_text_len: int) -> None:
    """Stretch every section forward to touch the next one, so separators
    between blocks are absorbed rather than left as coverage gaps."""
    for current, following in zip(sections, sections[1:]):
        current.char_end = following.char_start
    if sections:
        sections[-1].char_end = raw_text_len


def build_structure(blocks: list[Block], document_title: str | None = None) -> StructureResult:
    raw_text, offsets = _raw_text_and_offsets(blocks)

    if not blocks:
        title = document_title or _DEFAULT_TITLE
        return StructureResult(
            raw_text=raw_text,
            sections=[
                SectionDraft(
                    path="n1",
                    title=title,
                    display_path=title,
                    depth=1,
                    ordinal=1,
                    char_start=0,
                    char_end=0,
                )
            ],
        )

    has_any_heading = any(block["type"] == "heading" for block in blocks)
    leading_title = (document_title or _DEFAULT_TITLE) if not has_any_heading else "Preface"

    stack: list[_OpenHeading] = []
    sections: list[SectionDraft] = []
    leading_section: SectionDraft | None = None
    root_next_ordinal = 1

    for (start, end), block in zip(offsets, blocks):
        if block["type"] == "heading":
            level = block["level"]
            assert level is not None  # guaranteed by the Block IR contract

            while stack and stack[-1].level >= level:
                stack.pop()
            parent = stack[-1] if stack else None

            if parent is not None:
                ordinal = parent.next_child_ordinal
                parent.next_child_ordinal += 1
                path = f"{parent.draft.path}.n{ordinal}"
                display_path = f"{parent.draft.display_path} > {block['text']}"
                depth = parent.draft.depth + 1
            else:
                ordinal = root_next_ordinal
                root_next_ordinal += 1
                path = f"n{ordinal}"
                display_path = block["text"]
                depth = 1

            draft = SectionDraft(
                path=path,
                title=block["text"],
                display_path=display_path,
                depth=depth,
                ordinal=ordinal,
                char_start=start,
                char_end=end,
            )
            sections.append(draft)
            stack.append(_OpenHeading(level=level, draft=draft))
        elif stack:
            stack[-1].draft.char_end = end
        elif leading_section is None:
            leading_section = SectionDraft(
                path=f"n{root_next_ordinal}",
                title=leading_title,
                display_path=leading_title,
                depth=1,
                ordinal=root_next_ordinal,
                char_start=start,
                char_end=end,
            )
            root_next_ordinal += 1
            sections.append(leading_section)
        else:
            leading_section.char_end = end

    _close_gaps(sections, len(raw_text))
    return StructureResult(raw_text=raw_text, sections=sections)


async def persist_structure(
    db: AsyncSession, document: Document, result: StructureResult
) -> list[Section]:
    """Write a StructureResult's sections to the DB and set the document's
    raw_text. Assumes the document has no sections yet — not an upsert."""
    document.raw_text = result.raw_text
    rows = [
        Section(
            document_id=document.id,
            path=draft.path,
            title=draft.title,
            display_path=draft.display_path,
            depth=draft.depth,
            ordinal=draft.ordinal,
            char_start=draft.char_start,
            char_end=draft.char_end,
            source=StructureSource(draft.source),
        )
        for draft in result.sections
    ]
    db.add_all(rows)
    await db.flush()
    return rows
