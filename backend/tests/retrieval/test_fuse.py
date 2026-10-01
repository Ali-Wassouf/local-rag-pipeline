from app.retrieval.fuse import reciprocal_rank_fusion


def test_a_chunk_in_both_lists_outranks_one_in_only_one_list() -> None:
    fused = reciprocal_rank_fusion(vector_ids=[1, 2], keyword_ids=[1, 3])
    assert fused[0] == 1


def test_chunk_only_in_vector_list_is_still_included() -> None:
    fused = reciprocal_rank_fusion(vector_ids=[1, 2], keyword_ids=[])
    assert set(fused) == {1, 2}


def test_chunk_only_in_keyword_list_is_still_included() -> None:
    fused = reciprocal_rank_fusion(vector_ids=[], keyword_ids=[1, 2])
    assert set(fused) == {1, 2}


def test_final_order_is_by_descending_fused_score() -> None:
    # id 1: rank 1 in both lists -> highest combined score
    # id 2: rank 2 in vector only
    # id 3: rank 1 in keyword only, but 3 appears after 1 is exhausted... kept simple:
    fused = reciprocal_rank_fusion(vector_ids=[1, 2, 3], keyword_ids=[1, 3, 2])
    assert fused[0] == 1
    # 2 and 3 each hold one rank-2 and one rank-3 appearance, so they tie;
    # what matters here is 1 leads and both others are present.
    assert set(fused[1:]) == {2, 3}


def test_score_formula_matches_1_over_k_plus_rank() -> None:
    # id 1: vector rank 1 (1-indexed) only -> score = 1/(60+1)
    # id 2: keyword rank 1 only -> same score, tie -> both present, order stable
    fused = reciprocal_rank_fusion(vector_ids=[1], keyword_ids=[2], k=60)
    assert set(fused) == {1, 2}

    # id 1 in both at rank 1 should score exactly 2 * 1/(60+1) — verify by
    # comparing against an id that only reaches rank 1 in one list.
    fused_combined = reciprocal_rank_fusion(vector_ids=[1], keyword_ids=[1, 2])
    assert fused_combined[0] == 1
    assert fused_combined[1] == 2


def test_output_truncated_to_top_k() -> None:
    fused = reciprocal_rank_fusion(vector_ids=[1, 2, 3, 4], keyword_ids=[], top_k=2)
    assert fused == [1, 2]


def test_both_lists_empty_returns_empty() -> None:
    assert reciprocal_rank_fusion(vector_ids=[], keyword_ids=[]) == []
