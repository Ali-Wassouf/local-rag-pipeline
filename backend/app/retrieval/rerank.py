"""In-process cross-encoder reranking (docs/plan.md §4.3, §5) — run via
sentence-transformers/MPS, not Ollama, since it's not a generation model.
"""

import asyncio
from functools import lru_cache
from typing import cast

from sentence_transformers import CrossEncoder

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.section import Section

RERANKER_MODEL = "BAAI/bge-reranker-base"
DEFAULT_TOP_K = 8

Candidate = tuple[Chunk, Section, Document]


@lru_cache
def _load_reranker() -> CrossEncoder:
    return cast(CrossEncoder, CrossEncoder(RERANKER_MODEL))


def reranker_is_available() -> bool:
    try:
        _load_reranker()
        return True
    except Exception:
        return False


async def rerank(
    query: str,
    candidates: list[Candidate],
    top_k: int = DEFAULT_TOP_K,
) -> list[Candidate]:
    if not candidates:
        return []

    def _score_and_sort() -> list[Candidate]:
        model = _load_reranker()
        pairs = [(query, chunk.embed_text) for chunk, _section, _document in candidates]
        scores = model.predict(pairs)
        ranked = sorted(zip(scores, candidates), key=lambda item: item[0], reverse=True)
        return [candidate for _score, candidate in ranked[:top_k]]

    # CrossEncoder.predict is a blocking, CPU/MPS-bound call — run it off the
    # event loop so it doesn't stall other requests being served concurrently.
    return await asyncio.to_thread(_score_and_sort)
