import json

import httpx
import pytest

from app.retrieval.generate import rewrite_query


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://fake-ollama")


async def test_no_history_returns_question_unchanged_with_no_network_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("rewrite_query must not call Ollama when there is no history")

    client = _client(handler)
    try:
        result = await rewrite_query("What is a transaction?", history=[], client=client)
    finally:
        await client.aclose()

    assert result == "What is a transaction?"


async def test_with_history_returns_the_rewritten_text_from_ollama() -> None:
    body = json.dumps({"response": "What is serializable isolation?", "done": True})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        result = await rewrite_query(
            "What about the second one?",
            history=[
                ("user", "Name two isolation levels."),
                ("assistant", "Read Committed and Serializable."),
            ],
            client=client,
        )
    finally:
        await client.aclose()

    assert result == "What is serializable isolation?"


async def test_falls_back_to_original_question_on_failure_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="model not found")

    client = _client(handler)
    try:
        result = await rewrite_query(
            "What about the second one?",
            history=[("user", "Name two things."), ("assistant", "A and B.")],
            client=client,
        )
    finally:
        await client.aclose()

    assert result == "What about the second one?"


async def test_falls_back_to_original_question_on_inline_error_payload() -> None:
    body = json.dumps({"error": "model rag-gen not found"})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        result = await rewrite_query(
            "What about the second one?",
            history=[("user", "Name two things."), ("assistant", "A and B.")],
            client=client,
        )
    finally:
        await client.aclose()

    assert result == "What about the second one?"


async def test_real_ollama_rewrites_a_followup_into_a_standalone_question() -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip("Ollama is not running locally")

    result = await rewrite_query(
        "What about the second one?",
        history=[
            ("user", "Name two transaction isolation levels."),
            ("assistant", "Two common ones are Read Committed and Serializable."),
        ],
    )

    # Not asserting exact wording (a real model varies) — what matters is
    # that it actually pulled context from history rather than parroting
    # the pronoun-dependent question back unchanged.
    assert result.lower() != "what about the second one?"
    assert "isolation" in result.lower()
