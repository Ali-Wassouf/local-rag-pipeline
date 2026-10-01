"""The needle path (docs/plan.md §4.3): vector + keyword candidates, fused
by RRF, optionally reranked down to the final top-k.

`use_reranker=False` exists so evals can measure hybrid-vs-vector and
reranked-vs-unreranked *separately* (docs/build-phases.md Phase 4's
explicit "Done when") — it's an internal knob for that measurement, not a
user-facing setting.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.fuse import reciprocal_rank_fusion
from app.retrieval.rerank import DEFAULT_TOP_K as RERANK_TOP_K
from app.retrieval.rerank import Candidate, rerank
from app.retrieval.search import DEFAULT_CANDIDATE_K, keyword_search, vector_search


async def retrieve(
    db: AsyncSession,
    project_id: int,
    query_embedding: list[float],
    query_text: str,
    top_k: int = RERANK_TOP_K,
    candidate_k: int = DEFAULT_CANDIDATE_K,
    use_reranker: bool = True,
) -> list[Candidate]:
    # Sequential, not asyncio.gather: both share one AsyncSession, and a
    # single SQLAlchemy session cannot run two operations concurrently.
    vector_results = await vector_search(db, project_id, query_embedding, top_k=candidate_k)
    keyword_results = await keyword_search(db, project_id, query_text, top_k=candidate_k)

    by_id: dict[int, Candidate] = {}
    for chunk, section, document in (*vector_results, *keyword_results):
        by_id[chunk.id] = (chunk, section, document)

    fused_ids = reciprocal_rank_fusion(
        vector_ids=[chunk.id for chunk, _s, _d in vector_results],
        keyword_ids=[chunk.id for chunk, _s, _d in keyword_results],
        top_k=candidate_k,
    )
    fused = [by_id[chunk_id] for chunk_id in fused_ids]

    if not use_reranker:
        return fused[:top_k]

    return await rerank(query_text, fused, top_k=top_k)
