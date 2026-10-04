from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import Chunk
from app.models.conversation import Conversation
from app.models.document import DocFormat, Document, ProjectDocument
from app.models.section import Section


async def test_create_and_get_project(client: AsyncClient) -> None:
    created = await client.post("/projects", json={"name": "Physics", "description": None})
    assert created.status_code == 201
    project_id = created.json()["id"]

    fetched = await client.get(f"/projects/{project_id}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Physics"


async def test_list_projects_includes_created(client: AsyncClient) -> None:
    await client.post("/projects", json={"name": "Chemistry"})
    listed = await client.get("/projects")
    assert listed.status_code == 200
    names = [p["name"] for p in listed.json()]
    assert "Chemistry" in names


async def test_get_project_not_found(client: AsyncClient) -> None:
    response = await client.get("/projects/999999")
    assert response.status_code == 404


async def test_rename_project(client: AsyncClient) -> None:
    created = await client.post("/projects", json={"name": "Physics"})
    project_id = created.json()["id"]

    response = await client.patch(f"/projects/{project_id}", json={"name": "Quantum Physics"})
    assert response.status_code == 200
    assert response.json()["name"] == "Quantum Physics"

    fetched = await client.get(f"/projects/{project_id}")
    assert fetched.json()["name"] == "Quantum Physics"


async def test_rename_project_404s_for_unknown_project(client: AsyncClient) -> None:
    response = await client.patch("/projects/999999", json={"name": "Whatever"})
    assert response.status_code == 404


async def test_rename_project_rejects_an_empty_name(client: AsyncClient) -> None:
    created = await client.post("/projects", json={"name": "Physics"})
    project_id = created.json()["id"]

    response = await client.patch(f"/projects/{project_id}", json={"name": "   "})
    assert response.status_code == 422


async def test_delete_project(client: AsyncClient) -> None:
    created = await client.post("/projects", json={"name": "Temp"})
    project_id = created.json()["id"]

    deleted = await client.delete(f"/projects/{project_id}")
    assert deleted.status_code == 204

    missing = await client.get(f"/projects/{project_id}")
    assert missing.status_code == 404


async def test_delete_unknown_project_404s(client: AsyncClient) -> None:
    response = await client.delete("/projects/999999")
    assert response.status_code == 404


async def test_delete_project_does_not_delete_its_documents(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Deleting a project is a workspace-level action — the documents
    # themselves (and their sections/chunks) are a shared resource that may
    # belong to other projects too, so they must survive.
    created = await client.post("/projects", json={"name": "Temp"})
    project_id = created.json()["id"]

    document = Document(
        sha256="d" * 64,
        title="Survives Deletion",
        format=DocFormat.txt,
        original_name="d.txt",
        storage_path="/tmp/d.txt",
        raw_text="hello world",
    )
    db_session.add(document)
    await db_session.flush()
    section = Section(
        document_id=document.id,
        path="n1",
        title="T",
        display_path="T",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=11,
    )
    db_session.add(section)
    await db_session.flush()
    chunk = Chunk(
        document_id=document.id,
        section_id=section.id,
        ordinal=1,
        text="hello world",
        embed_text="hello world",
        char_start=0,
        char_end=11,
        token_count=2,
    )
    db_session.add(chunk)
    db_session.add(ProjectDocument(project_id=project_id, document_id=document.id))
    conversation = Conversation(project_id=project_id, title="A chat")
    db_session.add(conversation)
    await db_session.commit()
    document_id, chunk_id, conversation_id = document.id, chunk.id, conversation.id

    response = await client.delete(f"/projects/{project_id}")
    assert response.status_code == 204

    db_session.expire_all()
    assert await db_session.get(Document, document_id) is not None
    assert await db_session.get(Chunk, chunk_id) is not None
    # The project's own conversation is gone (meaningless without its
    # project), but the document it referenced is untouched.
    assert await db_session.get(Conversation, conversation_id) is None
