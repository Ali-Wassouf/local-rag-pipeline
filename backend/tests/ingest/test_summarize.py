import json

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.summarize import (
    SummarizationError,
    needs_summary,
    persist_section_summary,
    summarize_section,
)
from app.models.document import DocFormat, Document
from app.models.section import Section, StructureSource


async def _ollama_is_running() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://fake-ollama")


async def _make_document_with_section(db_session: AsyncSession, text: str = "x") -> Section:
    document = Document(
        sha256="s" * 64,
        title="Doc",
        format=DocFormat.txt,
        original_name="doc.txt",
        storage_path="/tmp/doc.txt",
        raw_text=text,
    )
    db_session.add(document)
    await db_session.flush()

    section = Section(
        document_id=document.id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=len(text),
        source=StructureSource.detected,
    )
    db_session.add(section)
    await db_session.flush()
    return section


# --- needs_summary -----------------------------------------------------


def test_needs_summary_is_false_below_the_threshold() -> None:
    assert needs_summary("a short section") is False


def test_needs_summary_is_true_above_the_threshold() -> None:
    long_text = "word " * 2000  # comfortably over 1500 tokens
    assert needs_summary(long_text) is True


# --- summarize_section (mocked Ollama) ----------------------------------


async def test_summarize_section_returns_the_generated_text() -> None:
    body = json.dumps({"response": "A concise summary.", "done": True})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        result = await summarize_section("Some long section text.", client=client)
    finally:
        await client.aclose()

    assert result == "A concise summary."


async def test_summarize_section_raises_on_failure_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="model not found")

    client = _client(handler)
    try:
        with pytest.raises(SummarizationError):
            await summarize_section("text", client=client)
    finally:
        await client.aclose()


async def test_summarize_section_raises_on_inline_error_payload() -> None:
    body = json.dumps({"error": "model rag-gen not found"})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        with pytest.raises(SummarizationError):
            await summarize_section("text", client=client)
    finally:
        await client.aclose()


async def test_real_ollama_summarizes_a_section() -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    # A ~200-word summary of a short paragraph can legitimately come out
    # *longer* than the source — the "shorter than input" property this
    # test checks only holds once the input is actually long, which is the
    # only case this function is ever called on in practice (needs_summary
    # gates it at >1500 tokens). So the test input has to be long for real,
    # not just topically on-point.
    paragraph = (
        "Serializable isolation is the strongest isolation level. It "
        "guarantees that even though transactions may execute in parallel, "
        "the result is the same as if they had executed one at a time, "
        "serially, without any concurrency. Databases implement it with "
        "techniques such as actual serial execution, two-phase locking, or "
        "serializable snapshot isolation. "
    )
    text = paragraph * 30
    assert needs_summary(text)

    summary = await summarize_section(text)
    assert len(summary) > 0
    assert len(summary) < len(text) / 2  # a real compression, not a restatement


# --- persist_section_summary (real DB) ----------------------------------


async def test_persist_section_summary_creates_a_new_row(db_session: AsyncSession) -> None:
    section = await _make_document_with_section(db_session)

    row = await persist_section_summary(
        db_session, section, "A summary.", [0.1] * 1024, model="rag-gen"
    )

    assert row.section_id == section.id
    assert row.document_id == section.document_id
    assert row.summary == "A summary."


async def test_persist_section_summary_upserts_rather_than_duplicates(
    db_session: AsyncSession,
) -> None:
    section = await _make_document_with_section(db_session)

    first = await persist_section_summary(
        db_session, section, "First summary.", [0.1] * 1024, model="rag-gen"
    )
    second = await persist_section_summary(
        db_session, section, "Second summary.", [0.2] * 1024, model="rag-gen"
    )

    assert first.id == second.id
    assert second.summary == "Second summary."
