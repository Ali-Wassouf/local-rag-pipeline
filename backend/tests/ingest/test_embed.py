import json

import httpx
import pytest

from app.ingest.embed import EMBEDDING_DIMENSION, EmbeddingError, embed_batch


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://fake-ollama")


async def test_embed_batch_returns_one_vector_per_text_same_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        embeddings = [[float(i)] * EMBEDDING_DIMENSION for i in range(len(body["input"]))]
        return httpx.Response(200, json={"embeddings": embeddings})

    client = _client(handler)
    try:
        result = await embed_batch(["alpha", "beta", "gamma"], client=client)
    finally:
        await client.aclose()

    assert len(result) == 3
    assert all(len(vec) == EMBEDDING_DIMENSION for vec in result)
    assert [vec[0] for vec in result] == [0.0, 1.0, 2.0]


async def test_embed_batch_splits_at_batch_boundary() -> None:
    call_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read())
        call_sizes.append(len(body["input"]))
        embeddings = [[0.0] * EMBEDDING_DIMENSION for _ in body["input"]]
        return httpx.Response(200, json={"embeddings": embeddings})

    client = _client(handler)
    try:
        result = await embed_batch([f"text-{i}" for i in range(33)], client=client)
    finally:
        await client.aclose()

    assert len(result) == 33
    assert call_sizes == [32, 1]


async def test_embed_batch_raises_clear_error_on_failure_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="model not found")

    client = _client(handler)
    try:
        with pytest.raises(EmbeddingError):
            await embed_batch(["x"], client=client)
    finally:
        await client.aclose()


async def test_embed_batch_empty_input_returns_empty_list() -> None:
    assert await embed_batch([]) == []


async def test_real_ollama_embed_returns_correct_dimension() -> None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip("Ollama is not running locally")

    result = await embed_batch(["dimension probe"])
    assert len(result) == 1
    assert len(result[0]) == EMBEDDING_DIMENSION
