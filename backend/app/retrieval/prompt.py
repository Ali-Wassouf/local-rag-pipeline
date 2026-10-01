"""Assembles the prompt sent to the generator: system instructions, numbered
sources, conversation history, then the current question.

Query rewriting for follow-ups happens before this, in
app/retrieval/generate.py's rewrite_query (docs/plan.md §4.2) — by the time
`question` gets here it's already standalone. Sources are expected to
already be breadcrumb-prefixed (chunks.embed_text), so they're inserted
verbatim rather than reassembled.
"""

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions using ONLY the sources "
    "below. Cite sources inline using [1], [2], etc., matching the source "
    "numbers. If the sources don't contain the answer, say so plainly."
)


def build_prompt(sources: list[str], history: list[tuple[str, str]], question: str) -> str:
    lines = [SYSTEM_PROMPT, ""]

    for rank, source_text in enumerate(sources, start=1):
        lines.append(f"[{rank}] {source_text}")
        lines.append("")

    for role, content in history:
        lines.append(f"{role.capitalize()}: {content}")

    lines.append(f"User: {question}")
    lines.append("Assistant:")
    return "\n".join(lines)
