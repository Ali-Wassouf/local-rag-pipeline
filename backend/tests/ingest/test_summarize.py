import json

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ingest.chunk import tokenizer
from app.ingest.summarize import (
    MAP_OUTPUT_TOKENS,
    MAX_SUMMARY_INPUT_TOKENS,
    SUMMARY_OUTPUT_TOKENS,
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


# --- summarize_section's map/reduce windowing (mocked Ollama) -----------


async def test_summarize_section_makes_a_single_call_for_text_within_budget() -> None:
    short_text = "a normal section, well within budget."
    captured_prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_prompts.append(json.loads(request.content)["prompt"])
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section(short_text, client=client)
    finally:
        await client.aclose()

    assert len(captured_prompts) == 1
    assert short_text in captured_prompts[0]


async def test_summarize_section_splits_oversized_text_into_multiple_windowed_calls() -> None:
    # A real book chapter routinely clears MAX_SUMMARY_INPUT_TOKENS (well
    # above the needs_summary qualify gate) — map/reduce is what covers
    # all of it instead of one oversized call.
    oversized_text = "word " * (MAX_SUMMARY_INPUT_TOKENS * 3)
    assert len(tokenizer().encode(oversized_text, add_special_tokens=False).ids) > (
        MAX_SUMMARY_INPUT_TOKENS * 2
    )

    captured_prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_prompts.append(json.loads(request.content)["prompt"])
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section(oversized_text, client=client)
    finally:
        await client.aclose()

    # Multiple map calls (one per window) plus one final reduce call.
    assert len(captured_prompts) > 2
    for map_prompt in captured_prompts[:-1]:
        token_count = len(tokenizer().encode(map_prompt, add_special_tokens=False).ids)
        assert token_count < MAX_SUMMARY_INPUT_TOKENS + 100  # template text adds a little
    assert "part 1 of" in captured_prompts[0].lower()
    # The reduce call's input is the map calls' outputs, not the raw text.
    assert "A summary." in captured_prompts[-1]


async def test_summarize_section_covers_the_whole_section_not_just_the_beginning() -> None:
    # The naive fix (truncate to budget) would silently drop everything
    # past the cutoff. Map/reduce must see all of it instead.
    filler = "filler " * MAX_SUMMARY_INPUT_TOKENS
    text = f"begin-marker {filler} middle-marker {filler} end-marker"

    captured_prompts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_prompts.append(json.loads(request.content)["prompt"])
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section(text, client=client)
    finally:
        await client.aclose()

    all_map_text = " ".join(captured_prompts[:-1])
    assert "begin-marker" in all_map_text
    assert "middle-marker" in all_map_text
    assert "end-marker" in all_map_text


async def test_summarize_section_disables_thinking() -> None:
    # rag-gen is a thinking model — with num_predict capped, a long enough
    # hidden thinking block can consume the whole budget before any answer
    # text is generated, leaving the response empty (a real incident: see
    # the "Ollama returned an empty summary" failures this caused in
    # production). think:false avoids that by skipping thinking outright.
    captured_bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_bodies.append(json.loads(request.content))
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section("some text", client=client)
    finally:
        await client.aclose()

    assert captured_bodies[0]["think"] is False


async def test_summarize_section_caps_output_length_for_a_single_window() -> None:
    captured_options: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_options
        captured_options = json.loads(request.content)["options"]
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section("some text", client=client)
    finally:
        await client.aclose()

    assert captured_options == {"num_predict": SUMMARY_OUTPUT_TOKENS}


async def test_summarize_section_caps_map_and_reduce_output_lengths_differently() -> None:
    oversized_text = "word " * (MAX_SUMMARY_INPUT_TOKENS * 3)
    captured_options: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_options.append(json.loads(request.content)["options"])
        return httpx.Response(200, content=json.dumps({"response": "A summary."}))

    client = _client(handler)
    try:
        await summarize_section(oversized_text, client=client)
    finally:
        await client.aclose()

    assert all(options == {"num_predict": MAP_OUTPUT_TOKENS} for options in captured_options[:-1])
    assert captured_options[-1] == {"num_predict": SUMMARY_OUTPUT_TOKENS}


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


async def test_real_ollama_summarizes_a_section_that_needs_multiple_windows() -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    paragraph = (
        "Serializable isolation is the strongest isolation level. It "
        "guarantees that even though transactions may execute in parallel, "
        "the result is the same as if they had executed one at a time, "
        "serially, without any concurrency. Databases implement it with "
        "techniques such as actual serial execution, two-phase locking, or "
        "serializable snapshot isolation. "
    )
    # ~141 repeats lands just over 2x MAX_SUMMARY_INPUT_TOKENS, forcing the
    # map/reduce path (2 windows) rather than the single-call path that
    # the other real-Ollama test already covers.
    text = paragraph * 141
    token_count = len(tokenizer().encode(text, add_special_tokens=False).ids)
    assert token_count > MAX_SUMMARY_INPUT_TOKENS

    summary = await summarize_section(text)
    assert len(summary) > 0
    assert len(summary) < len(text) / 2


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
