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


REWRITE_SYSTEM_PROMPT = (
    "Rewrite the user's latest message as a standalone question that does not "
    "rely on the conversation above. Reply with ONLY the rewritten question, "
    "nothing else."
)


def _build_rewrite_prompt(question: str, history: list[tuple[str, str]]) -> str:
    lines = [REWRITE_SYSTEM_PROMPT, ""]
    for role, content in history:
        lines.append(f"{role.capitalize()}: {content}")
    lines.append(f"Latest message: {question}")
    lines.append("Standalone question:")
    return "\n".join(lines)


async def rewrite_query(
    question: str,
    history: list[tuple[str, str]],
    client: httpx.AsyncClient | None = None,
) -> str:
    """Turns a context-dependent follow-up ("what about the second one?")
    into a standalone query before retrieval (docs/plan.md §4.2).

    Skipped entirely on the first turn of a conversation (no history to
    resolve against, and no reason to risk mangling an already-standalone
    question). On any failure — Ollama down, a bad response — falls back to
    the original question rather than failing the request: rewriting is an
    enhancement to retrieval, not a hard requirement.
    """
    if not history:
        return question

    settings = get_settings()
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=30.0)

    try:
        response = await active_client.post(
            "/api/generate",
            json={
                "model": settings.generation_model,
                "prompt": _build_rewrite_prompt(question, history),
                "stream": False,
            },
        )
        if response.status_code != 200:
            return question
        data = response.json()
        if data.get("error"):
            return question
        rewritten = str(data.get("response", "")).strip()
        return rewritten or question
    except (httpx.HTTPError, json.JSONDecodeError):
        return question
    finally:
        if owns_client:
            await active_client.aclose()
