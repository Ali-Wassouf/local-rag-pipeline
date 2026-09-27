"""Async client for Ollama's embed endpoint.

Calls Ollama over HTTP rather than loading the model in-process — see
docs/plan.md's model table and setup-env.sh, which pulls the embedder
(qwen3-embedding:0.6b) into Ollama, and OLLAMA_MAX_LOADED_MODELS=1, which
only makes sense if the embedder shares Ollama's one resident-model slot
with the generator.
"""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.embedding_run import EmbeddingRun

EMBEDDING_DIMENSION = 1024
_BATCH_SIZE = 32


class EmbeddingError(Exception):
    """Raised when Ollama's embed endpoint fails or returns something unexpected."""


async def embed_batch(
    texts: list[str], client: httpx.AsyncClient | None = None
) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()
    owns_client = client is None
    active_client = client or httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=60.0)

    try:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            response = await active_client.post(
                "/api/embed",
                json={"model": settings.embedding_model, "input": batch},
            )
            if response.status_code != 200:
                raise EmbeddingError(
                    f"Ollama embed request failed ({response.status_code}): {response.text}"
                )
            data = response.json()
            batch_embeddings = data.get("embeddings")
            if not isinstance(batch_embeddings, list):
                raise EmbeddingError(f"Ollama embed response missing 'embeddings': {data}")
            embeddings.extend(batch_embeddings)
        return embeddings
    finally:
        if owns_client:
            await active_client.aclose()


async def get_or_create_embedding_run(
    db: AsyncSession, model: str, dimension: int
) -> EmbeddingRun:
    """One row per (model, dimension). Swapping embedders is a deliberate,
    manual re-index per docs/plan.md — this doesn't demote old runs."""
    existing = await db.execute(
        select(EmbeddingRun).where(EmbeddingRun.model == model, EmbeddingRun.is_current.is_(True))
    )
    run = existing.scalar_one_or_none()
    if run is not None:
        return run

    run = EmbeddingRun(model=model, dimension=dimension, is_current=True)
    db.add(run)
    await db.flush()
    return run
