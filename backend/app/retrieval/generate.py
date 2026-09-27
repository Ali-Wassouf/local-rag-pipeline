"""Streaming client for Ollama's generate endpoint (the `rag-gen` model —
qwen3:8b with num_ctx/num_batch/temperature baked in, see setup-env.sh).

Same pattern as app/ingest/embed.py: HTTP to Ollama, not an in-process model.
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.core.config import get_settings


class GenerationError(Exception):
    """Raised when Ollama's generate endpoint fails or returns something unexpected."""


async def stream_generate(
    prompt: str, client: httpx.AsyncClient | None = None
) -> AsyncIterator[str]:
    settings = get_settings()
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120.0)

    try:
        async with active_client.stream(
            "POST",
            "/api/generate",
            json={"model": settings.generation_model, "prompt": prompt, "stream": True},
        ) as response:
            if response.status_code != 200:
                body = await response.aread()
                raise GenerationError(
                    f"Ollama generate request failed ({response.status_code}): {body.decode()}"
                )
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise GenerationError(f"Ollama generate error: {data['error']}")
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
    finally:
        if owns_client:
            await active_client.aclose()
