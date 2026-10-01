"""Chunker: splits a section's text into overlapping token windows.

A flat token-window slide, not sentence-aware — the 700/100 budget math in
docs/plan.md §8 assumes flat token counting, and boundary-snapping is the
kind of tuning that doc says to defer until there's a query set to measure
against.

Token counting uses the real embedder's tokenizer (Qwen3-Embedding-0.6B),
not an approximation — this is exactly the "once we know the actual
tokenizer" moment app/ingest/review.py's char-count placeholder flagged.
"""

from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession
from tokenizers import Tokenizer

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.section import Section

TOKENIZER_MODEL = "Qwen/Qwen3-Embedding-0.6B"

# Committed defaults from docs/plan.md §8 — do not tune without a query set.
CHUNK_TOKENS = 700
CHUNK_OVERLAP_TOKENS = 100
_CHUNK_STRIDE = CHUNK_TOKENS - CHUNK_OVERLAP_TOKENS


@lru_cache(maxsize=1)
def tokenizer() -> Tokenizer:
    return Tokenizer.from_pretrained(TOKENIZER_MODEL)


@dataclass
class ChunkDraft:
    ordinal: int
    text: str
    embed_text: str
    char_start: int
    char_end: int
    token_count: int


def chunk_section(
    display_path: str, section_text: str, section_char_offset: int
) -> list[ChunkDraft]:
    """Slide a 700-token/100-overlap window over one section's text.

    `section_char_offset` is where this section starts in the document's
    raw_text, so returned offsets are absolute, not section-local.
    """
    encoding = tokenizer().encode(section_text, add_special_tokens=False)
    offsets = encoding.offsets
    total = len(offsets)
    if total == 0:
        return []

    drafts: list[ChunkDraft] = []
    ordinal = 1
    start_token = 0
    while True:
        end_token = min(start_token + CHUNK_TOKENS, total)
        local_start = offsets[start_token][0]
        local_end = offsets[end_token - 1][1]
        text = section_text[local_start:local_end]

        drafts.append(
            ChunkDraft(
                ordinal=ordinal,
                text=text,
                embed_text=f"{display_path}\n\n{text}",
                char_start=section_char_offset + local_start,
                char_end=section_char_offset + local_end,
                token_count=end_token - start_token,
            )
        )

        if end_token == total:
            break
        ordinal += 1
        start_token += _CHUNK_STRIDE

    return drafts


async def persist_chunks(
    db: AsyncSession, document: Document, sections: list[Section]
) -> list[Chunk]:
    """Chunk every section and write the resulting rows. embedding and
    embedding_run_id are left NULL — that's the embed stage's job."""
    raw_text = document.raw_text or ""
    rows: list[Chunk] = []
    for section in sections:
        section_text = raw_text[section.char_start : section.char_end]
        for draft in chunk_section(section.display_path, section_text, section.char_start):
            rows.append(
                Chunk(
                    document_id=document.id,
                    section_id=section.id,
                    ordinal=draft.ordinal,
                    text=draft.text,
                    embed_text=draft.embed_text,
                    char_start=draft.char_start,
                    char_end=draft.char_end,
                    token_count=draft.token_count,
                )
            )
    db.add_all(rows)
    await db.flush()
    return rows
