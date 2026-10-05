"""Section summarisation for the survey path (docs/plan.md §2.5, §4.4, §8).

Calls the generate endpoint (rag-gen) over HTTP, same pattern as
app/retrieval/generate.py — there's no separate summariser model in
docs/plan.md's model table, so this reuses the one generator already
resident in Ollama.
"""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.ingest.chunk import tokenizer
from app.models.section import Section
from app.models.summary import SectionSummary

# Committed default from docs/plan.md §8 — do not tune without a query set.
# This is the qualify gate ("is this section worth summarising at all"),
# distinct from MAX_SUMMARY_INPUT_TOKENS below ("how much of it can
# actually be sent") — a section can clear this threshold by a wide margin
# (a real book chapter is routinely 10-20k+ tokens) while still needing to
# be capped before it reaches the model.
SUMMARY_THRESHOLD_TOKENS = 1500

# rag-gen's context window (scripts/setup-env.sh bakes num_ctx=8192 into the
# Modelfile). Reserved budget leaves room for the prompt template plus the
# output; what's left (MAX_SUMMARY_INPUT_TOKENS) is the window size a
# section gets split into when it doesn't fit in one call — see
# _split_into_windows and the map/reduce summarise_section below. Without
# this, a long chapter would silently overflow the context and trigger
# Ollama's own --context-shift, which is both slow (repeated reprocessing
# of a huge prompt) and produces a summary of only the tail of the
# chapter, since the opening is what gets shifted out first.
_GENERATOR_CONTEXT_TOKENS = 8192
SUMMARY_OUTPUT_TOKENS = 500  # generous headroom over the ~200-word target
MAP_OUTPUT_TOKENS = 300  # headroom over each part's ~120-word target
_PROMPT_TEMPLATE_RESERVE_TOKENS = 200  # template text + chat-template overhead
MAX_SUMMARY_INPUT_TOKENS = (
    _GENERATOR_CONTEXT_TOKENS - SUMMARY_OUTPUT_TOKENS - _PROMPT_TEMPLATE_RESERVE_TOKENS
)

SUMMARY_PROMPT = (
    "Summarise the following section in about 200 words. Capture its key "
    "claims and conclusions. Do not add information that isn't in the "
    "text.\n\n{text}\n\nSummary:"
)

# Used instead of SUMMARY_PROMPT when a section doesn't fit in one window —
# "part N of M" tells the model it's reading an excerpt, not the whole
# thing, so it doesn't treat an abrupt start/end as the section's own.
MAP_PROMPT = (
    "The following is part {index} of {total} of a longer section, in "
    "order. Summarise this part in about 120 words, capturing its key "
    "claims and conclusions. Do not add information that isn't in the "
    "text.\n\n{text}\n\nSummary:"
)

# Combines the per-window summaries from MAP_PROMPT into one final summary
# — this is what actually covers the whole section, since each window was
# already a bounded, complete pass over its own slice of the text.
REDUCE_PROMPT = (
    "The following are summaries of consecutive parts of the same "
    "section, in order. Combine them into one coherent summary of about "
    "200 words that captures the section's key claims and conclusions as "
    "a whole. Do not add information that isn't in the text.\n\n{text}\n\n"
    "Summary:"
)


class SummarizationError(Exception):
    """Raised when Ollama's generate endpoint fails or returns something
    unexpected while summarising."""


def needs_summary(section_text: str) -> bool:
    """Below the threshold a section is only a chunk or two, already close
    to being its own summary — summarising adds ingest time and no
    retrieval value (docs/plan.md §8)."""
    token_count = len(tokenizer().encode(section_text, add_special_tokens=False).ids)
    return token_count > SUMMARY_THRESHOLD_TOKENS


def _split_into_windows(text: str, max_tokens: int) -> list[str]:
    """Non-overlapping token windows covering the whole text. Each window
    is summarised independently (the "map" step below) and then combined,
    so — unlike the retrieval chunker — there's no need for overlap here;
    we're not trying to avoid splitting a fact across a boundary for
    search, just to cover everything exactly once."""
    offsets = tokenizer().encode(text, add_special_tokens=False).offsets
    total = len(offsets)
    if total <= max_tokens:
        return [text]

    windows: list[str] = []
    start = 0
    while start < total:
        end = min(start + max_tokens, total)
        windows.append(text[offsets[start][0] : offsets[end - 1][1]])
        start = end
    return windows


async def _generate(
    prompt: str, num_predict: int, settings: Settings, client: httpx.AsyncClient
) -> str:
    response = await client.post(
        "/api/generate",
        json={
            "model": settings.generation_model,
            "prompt": prompt,
            "stream": False,
            # rag-gen (qwen3) is a thinking model — it reasons in a hidden
            # block before the visible answer. With num_predict capped,
            # a long enough thinking block can consume the whole budget
            # before any answer text is generated, leaving `response`
            # empty. We only ever want the final text here, never the
            # reasoning trace, so thinking is switched off outright —
            # that also removes a chunk of wasted generation time.
            "think": False,
            "options": {"num_predict": num_predict},
        },
    )
    if response.status_code != 200:
        raise SummarizationError(
            f"Ollama generate request failed ({response.status_code}): {response.text}"
        )
    data = response.json()
    if data.get("error"):
        raise SummarizationError(f"Ollama generate error: {data['error']}")
    summary = str(data.get("response", "")).strip()
    if not summary:
        raise SummarizationError("Ollama returned an empty summary")
    return summary


async def summarize_section(
    section_text: str, client: httpx.AsyncClient | None = None
) -> str:
    """Summarises the whole section, however long it is.

    A section that fits in one context window (the common case) gets
    exactly the single call this always made. A section too long for that
    — a real book chapter routinely clears MAX_SUMMARY_INPUT_TOKENS — is
    split into windows (map), each summarised on its own, then those
    partial summaries are combined into one final summary (reduce). That's
    what makes the summary cover the whole chapter instead of silently
    truncating it.
    """
    settings = get_settings()
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)

    try:
        windows = _split_into_windows(section_text, MAX_SUMMARY_INPUT_TOKENS)
        if len(windows) == 1:
            return await _generate(
                SUMMARY_PROMPT.format(text=windows[0]),
                SUMMARY_OUTPUT_TOKENS,
                settings,
                active_client,
            )

        partial_summaries = [
            await _generate(
                MAP_PROMPT.format(index=i + 1, total=len(windows), text=window),
                MAP_OUTPUT_TOKENS,
                settings,
                active_client,
            )
            for i, window in enumerate(windows)
        ]
        combined = "\n\n".join(partial_summaries)
        return await _generate(
            REDUCE_PROMPT.format(text=combined),
            SUMMARY_OUTPUT_TOKENS,
            settings,
            active_client,
        )
    finally:
        if owns_client:
            await active_client.aclose()


async def persist_section_summary(
    db: AsyncSession,
    section: Section,
    summary_text: str,
    embedding: list[float],
    model: str,
) -> SectionSummary:
    """Upsert — section_id is unique, so re-running this (e.g. the backfill
    command) replaces rather than duplicates."""
    existing = await db.execute(
        select(SectionSummary).where(SectionSummary.section_id == section.id)
    )
    row = existing.scalar_one_or_none()
    if row is None:
        row = SectionSummary(
            section_id=section.id,
            document_id=section.document_id,
            summary=summary_text,
            embedding=embedding,
            model=model,
        )
        db.add(row)
    else:
        row.summary = summary_text
        row.embedding = embedding
        row.model = model
    await db.flush()
    return row
