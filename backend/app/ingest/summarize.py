"""Section summarisation for the survey path (docs/plan.md §2.5, §4.4, §8).

Calls the generate endpoint (rag-gen) over HTTP, same pattern as
app/retrieval/generate.py — there's no separate summariser model in
docs/plan.md's model table, so this reuses the one generator already
resident in Ollama.
"""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.ingest.chunk import tokenizer
from app.models.section import Section
from app.models.summary import SectionSummary

# Committed default from docs/plan.md §8 — do not tune without a query set.
SUMMARY_THRESHOLD_TOKENS = 1500

SUMMARY_PROMPT = (
    "Summarise the following section in about 200 words. Capture its key "
    "claims and conclusions. Do not add information that isn't in the "
    "text.\n\n{text}\n\nSummary:"
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


async def summarize_section(
    section_text: str, client: httpx.AsyncClient | None = None
) -> str:
    settings = get_settings()
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)

    try:
        response = await active_client.post(
            "/api/generate",
            json={
                "model": settings.generation_model,
                "prompt": SUMMARY_PROMPT.format(text=section_text),
                "stream": False,
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
