from app.retrieval.prompt import build_prompt


def test_sources_appear_verbatim_and_numbered_from_one() -> None:
    prompt = build_prompt(
        sources=["Ch. 1 > Intro\n\nFirst source body.", "Ch. 2 > Storage\n\nSecond source body."],
        history=[],
        question="What is this book about?",
    )
    assert "[1] Ch. 1 > Intro\n\nFirst source body." in prompt
    assert "[2] Ch. 2 > Storage\n\nSecond source body." in prompt


def test_history_appears_in_order() -> None:
    prompt = build_prompt(
        sources=["source"],
        history=[("user", "What is X?"), ("assistant", "X is Y.")],
        question="And what about Z?",
    )
    user_pos = prompt.index("User: What is X?")
    assistant_pos = prompt.index("Assistant: X is Y.")
    question_pos = prompt.index("User: And what about Z?")
    assert user_pos < assistant_pos < question_pos


def test_question_is_the_final_user_turn_followed_by_assistant_cue() -> None:
    prompt = build_prompt(sources=["source"], history=[], question="Hello?")
    assert prompt.rstrip().endswith("User: Hello?\nAssistant:")


def test_no_history_does_not_crash_or_leave_stray_markers() -> None:
    prompt = build_prompt(sources=["source"], history=[], question="Q")
    assert "User: Q" in prompt
