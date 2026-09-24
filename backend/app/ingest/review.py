"""Pure helpers for the structure review screen: preview text, a chunk/token
estimate, and gap ("untitled region") detection. No DB access here.
"""

import math
from typing import Protocol

from app.ingest.structure import SectionDraft

# Placeholder until Phase 2 wires the real embedding-model tokenizer.
# Revisit once we know the actual tokenizer's char/token ratio.
_CHARS_PER_TOKEN = 4

# Matches docs/plan.md §8's committed chunking constants.
_CHUNK_TOKENS = 700
_CHUNK_OVERLAP_TOKENS = 100

PREVIEW_MAX_CHARS = 300


class _HasCharRange(Protocol):
    char_start: int
    char_end: int


def section_preview(raw_text: str, section: _HasCharRange, max_chars: int) -> str:
    text = raw_text[section.char_start : section.char_end]
    return text[:max_chars]


def estimate_chunks(text: str) -> int:
    if not text:
        return 0
    token_count = len(text) / _CHARS_PER_TOKEN
    if token_count <= _CHUNK_TOKENS:
        return 1
    stride = _CHUNK_TOKENS - _CHUNK_OVERLAP_TOKENS
    return 1 + math.ceil((token_count - _CHUNK_TOKENS) / stride)


def find_uncovered_ranges(
    raw_text_len: int, sections: list[SectionDraft]
) -> list[tuple[int, int]]:
    """Character ranges in [0, raw_text_len) not covered by any section.
    Ignores overlaps — this only reports under-coverage, not double-coverage.
    """
    if not sections:
        return [(0, raw_text_len)] if raw_text_len > 0 else []

    ordered = sorted(sections, key=lambda s: s.char_start)
    gaps: list[tuple[int, int]] = []

    cursor = 0
    for section in ordered:
        if section.char_start > cursor:
            gaps.append((cursor, section.char_start))
        cursor = max(cursor, section.char_end)

    if cursor < raw_text_len:
        gaps.append((cursor, raw_text_len))

    return gaps
