import json
import uuid

import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.document import DocFormat, Document, ProjectDocument
from app.models.project import Project
from app.models.section import Section


async def _ollama_is_running() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as probe:
            response = await probe.get("http://localhost:11434/api/tags")
            response.raise_for_status()
        return True
    except httpx.HTTPError:
        return False


async def _create_project(client: AsyncClient, name: str = "Physics") -> int:
    response = await client.post("/projects", json={"name": name})
    id_value: int = response.json()["id"]
    return id_value


def _parse_sse_events(text: str) -> list[dict]:
    events = []
    for block in text.strip().split("\n\n"):
        block = block.strip()
        if not block:
            continue
        assert block.startswith("data: ")
        events.append(json.loads(block.removeprefix("data: ")))
    return events


async def _seed_embedded_chunk(
    db_session: AsyncSession, project_id: int, text: str, embedding: list[float]
) -> Chunk:
    document = Document(
        sha256=(uuid.uuid4().hex + uuid.uuid4().hex),
        title=f"Doc about {text[:20]}",
        format=DocFormat.txt,
        original_name="d.txt",
        storage_path="/tmp/d.txt",
        raw_text=text,
    )
    db_session.add(document)
    await db_session.flush()
    db_session.add(ProjectDocument(project_id=project_id, document_id=document.id))

    section = Section(
        document_id=document.id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=len(text),
    )
    db_session.add(section)
    await db_session.flush()

    chunk = Chunk(
        document_id=document.id,
        section_id=section.id,
        ordinal=1,
        text=text,
        embed_text=f"T\n\n{text}",
        char_start=0,
        char_end=len(text),
        token_count=len(text.split()),
        embedding=embedding,
    )
    db_session.add(chunk)
    await db_session.flush()
    return chunk


# --- conversation/message CRUD, no Ollama needed ---------------------------


async def test_create_conversation(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.post(f"/projects/{project_id}/conversations")
    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


async def test_create_conversation_404s_for_unknown_project(client: AsyncClient) -> None:
    response = await client.post("/projects/999999/conversations")
    assert response.status_code == 404


async def test_list_conversations_for_project(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    await client.post(f"/projects/{project_id}/conversations")
    await client.post(f"/projects/{project_id}/conversations")

    response = await client.get(f"/projects/{project_id}/conversations")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_list_conversations_404s_for_unknown_project(client: AsyncClient) -> None:
    response = await client.get("/projects/999999/conversations")
    assert response.status_code == 404


async def test_list_messages_is_empty_for_a_fresh_conversation(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    created = await client.post(f"/projects/{project_id}/conversations")
    conversation_id = created.json()["id"]

    response = await client.get(f"/conversations/{conversation_id}/messages")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_messages_404s_for_unknown_conversation(client: AsyncClient) -> None:
    response = await client.get("/conversations/999999/messages")
    assert response.status_code == 404


async def test_send_message_404s_for_unknown_conversation(client: AsyncClient) -> None:
    response = await client.post("/conversations/999999/messages", json={"content": "hi"})
    assert response.status_code == 404


# --- full send-message flow, needs real Ollama (embed + generate) ---------


async def test_send_message_persists_and_streams(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    project_id = await _create_project(client, "Chat Project")
    chunk = await _seed_embedded_chunk(
        db_session,
        project_id,
        "The mitochondria is the powerhouse of the cell.",
        [0.1] * 1024,
    )
    await db_session.commit()

    created = await client.post(f"/projects/{project_id}/conversations")
    conversation_id = created.json()["id"]

    response = await client.post(
        f"/conversations/{conversation_id}/messages",
        json={"content": "What is the powerhouse of the cell?"},
    )
    assert response.status_code == 200
    events = _parse_sse_events(response.text)

    token_events = [e for e in events if "token" in e]
    final_events = [e for e in events if e.get("done")]
    assert len(token_events) >= 1, "answer should stream as multiple token events"
    assert len(final_events) == 1

    citations = final_events[0]["citations"]
    assert len(citations) >= 1
    assert citations[0]["chunk_id"] == chunk.id

    history = await client.get(f"/conversations/{conversation_id}/messages")
    messages = history.json()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "What is the powerhouse of the cell?"
    assert messages[1]["citations"][0]["chunk_id"] == chunk.id


async def test_chat_never_cites_another_projects_chunks(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    if not await _ollama_is_running():
        pytest.skip("Ollama is not running locally")

    project_a = await _create_project(client, "Project A")
    project_b = await _create_project(client, "Project B")

    await _seed_embedded_chunk(db_session, project_a, "Cats are small domesticated mammals.", [0.2] * 1024)
    chunk_b = await _seed_embedded_chunk(
        db_session, project_b, "Cats are small domesticated mammals.", [0.2] * 1024
    )
    await db_session.commit()

    created = await client.post(f"/projects/{project_a}/conversations")
    conversation_id = created.json()["id"]

    response = await client.post(
        f"/conversations/{conversation_id}/messages", json={"content": "Tell me about cats."}
    )
    events = _parse_sse_events(response.text)
    final = next(e for e in events if e.get("done"))
    cited_ids = [c["chunk_id"] for c in final["citations"]]
    assert chunk_b.id not in cited_ids
