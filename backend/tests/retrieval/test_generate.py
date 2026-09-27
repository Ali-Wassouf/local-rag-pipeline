import json

import httpx
import pytest

from app.retrieval.generate import GenerationError, stream_generate


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://fake-ollama")


async def test_stream_generate_yields_tokens_as_they_arrive() -> None:
    body = "\n".join(
        [
            json.dumps({"response": "Hello", "done": False}),
            json.dumps({"response": " world", "done": False}),
            json.dumps({"response": "", "done": True}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        tokens = [t async for t in stream_generate("prompt", client=client)]
    finally:
        await client.aclose()

    assert tokens == ["Hello", " world"]


async def test_stream_generate_raises_clear_error_on_failure_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="model not found")

    client = _client(handler)
    try:
        with pytest.raises(GenerationError):
            async for _ in stream_generate("prompt", client=client):
                pass
    finally:
        await client.aclose()


async def test_stream_generate_raises_on_inline_error_payload() -> None:
    body = json.dumps({"error": "model rag-gen not found"})

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    client = _client(handler)
    try:
        with pytest.raises(GenerationError):
            async for _ in stream_generate("prompt", client=client):
                pass
    finally:
        await client.aclose()


async def test_real_ollama_generate_streams_tokens() -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip("Ollama is not running locally")

    tokens = [t async for t in stream_generate("Reply with exactly the word: ok")]
    assert len(tokens) >= 1
    assert "".join(tokens).strip() != ""
