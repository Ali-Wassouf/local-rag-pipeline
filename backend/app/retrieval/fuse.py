"""Reciprocal rank fusion — combines the vector and keyword candidate lists
into one ranking (docs/plan.md §4.3). Pure function: operates on chunk ids
only, ranks are 1-indexed by each list's own order, and the caller resolves
ids back to full rows.
"""

DEFAULT_RRF_K = 60
DEFAULT_TOP_K = 50


def reciprocal_rank_fusion(
    vector_ids: list[int],
    keyword_ids: list[int],
    k: int = DEFAULT_RRF_K,
    top_k: int = DEFAULT_TOP_K,
) -> list[int]:
    scores: dict[int, float] = {}
    for ids in (vector_ids, keyword_ids):
        for rank, chunk_id in enumerate(ids, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    ordered = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)
    return ordered[:top_k]
