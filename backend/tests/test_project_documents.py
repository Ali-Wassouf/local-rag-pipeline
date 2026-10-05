from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import IngestJob, JobStage
from app.models.section import Section
from app.models.summary import SectionSummary


async def _create_project(client: AsyncClient, name: str = "Physics") -> int:
    response = await client.post("/projects", json={"name": name})
    id_value: int = response.json()["id"]
    return id_value


async def _create_document(
    client: AsyncClient, filename: str = "a.txt", content: bytes = b"hello"
) -> int:
    response = await client.post("/documents", files={"file": (filename, content, "text/plain")})
    id_value: int = response.json()["document"]["id"]
    return id_value


async def test_list_documents_for_project_is_empty_initially(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.get(f"/projects/{project_id}/documents")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_documents_404s_for_unknown_project(client: AsyncClient) -> None:
    response = await client.get("/projects/999999/documents")
    assert response.status_code == 404


async def test_attach_document_to_project(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)

    response = await client.post(
        f"/projects/{project_id}/documents", json={"document_id": document_id}
    )
    assert response.status_code == 201

    listed = await client.get(f"/projects/{project_id}/documents")
    ids = [d["id"] for d in listed.json()]
    assert document_id in ids


async def test_list_only_shows_documents_attached_to_that_project(client: AsyncClient) -> None:
    project_a = await _create_project(client, "A")
    project_b = await _create_project(client, "B")
    doc_a = await _create_document(client, "a.txt", b"content a")
    doc_b = await _create_document(client, "b.txt", b"content b")

    await client.post(f"/projects/{project_a}/documents", json={"document_id": doc_a})
    await client.post(f"/projects/{project_b}/documents", json={"document_id": doc_b})

    listed_a = await client.get(f"/projects/{project_a}/documents")
    ids_a = [d["id"] for d in listed_a.json()]
    assert doc_a in ids_a
    assert doc_b not in ids_a


async def test_attach_document_is_idempotent(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)

    first = await client.post(
        f"/projects/{project_id}/documents", json={"document_id": document_id}
    )
    second = await client.post(
        f"/projects/{project_id}/documents", json={"document_id": document_id}
    )
    assert first.status_code == 201
    assert second.status_code == 201

    listed = await client.get(f"/projects/{project_id}/documents")
    ids = [d["id"] for d in listed.json()]
    assert ids.count(document_id) == 1


async def test_attach_404s_for_unknown_project(client: AsyncClient) -> None:
    document_id = await _create_document(client)
    response = await client.post("/projects/999999/documents", json={"document_id": document_id})
    assert response.status_code == 404


async def test_attach_404s_for_unknown_document(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    response = await client.post(f"/projects/{project_id}/documents", json={"document_id": 999999})
    assert response.status_code == 404


async def test_detach_document_removes_the_link_not_the_document(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})

    response = await client.delete(f"/projects/{project_id}/documents/{document_id}")
    assert response.status_code == 204

    listed = await client.get(f"/projects/{project_id}/documents")
    assert document_id not in [d["id"] for d in listed.json()]

    still_exists = await client.get(f"/documents/{document_id}")
    assert still_exists.status_code == 200


async def test_detach_404s_when_link_does_not_exist(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    response = await client.delete(f"/projects/{project_id}/documents/{document_id}")
    assert response.status_code == 404


# --- section/summary counts (so the UI can tell "opted in but nothing ---
# --- qualified" apart from "has real summaries", docs/plan.md §8) -------


async def test_lists_section_and_summary_counts_for_a_document(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})

    summarized = Section(
        document_id=document_id,
        path="n1",
        title="Summarized",
        display_path="Summarized",
        depth=1,
        ordinal=1,
        char_start=0,
        char_end=1,
    )
    unsummarized = Section(
        document_id=document_id,
        path="n2",
        title="Unsummarized",
        display_path="Unsummarized",
        depth=1,
        ordinal=2,
        char_start=1,
        char_end=2,
    )
    db_session.add_all([summarized, unsummarized])
    await db_session.flush()
    db_session.add(
        SectionSummary(
            section_id=summarized.id,
            document_id=document_id,
            summary="a summary",
            embedding=[0.1] * 1024,
            model="rag-gen",
        )
    )
    await db_session.commit()

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["section_count"] == 2
    assert body["summary_count"] == 1


async def test_section_and_summary_counts_are_zero_for_an_unprocessed_document(
    client: AsyncClient,
) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["section_count"] == 0
    assert body["summary_count"] == 0


async def test_summarizing_is_true_while_a_summarise_job_is_pending_or_running(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # summary_count==0 alone can't tell "hasn't finished yet" apart from
    # "genuinely nothing qualified" — a document can reach status=ready
    # (chat-usable) while summarise is still pending or actively running in
    # the background, since embedding finishing is what makes it ready.
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})
    db_session.add(
        IngestJob(document_id=document_id, stage=JobStage.summarise.value, progress=1.0)
    )
    await db_session.commit()

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["summarizing"] is True


async def test_summary_total_reflects_the_in_progress_jobs_qualifying_count(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # summary_count (persisted rows) is already the live "done so far"
    # number — this is the other half of "N of M" progress, the
    # denominator the job determined on its first tick.
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})
    db_session.add(
        IngestJob(
            document_id=document_id,
            stage=JobStage.summarise.value,
            progress=2 / 5,
            summary_done=2,
            summary_total=5,
        )
    )
    await db_session.commit()

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["summary_total"] == 5


async def test_summary_total_is_null_without_an_in_progress_job(
    client: AsyncClient,
) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["summary_total"] is None


async def test_summarizing_is_false_once_the_job_finishes(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})
    db_session.add(
        IngestJob(
            document_id=document_id,
            stage=JobStage.done.value,
            progress=1.0,
            finished_at=datetime.now(UTC),
        )
    )
    await db_session.commit()

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["summarizing"] is False


async def test_summarizing_is_false_without_any_job(client: AsyncClient) -> None:
    project_id = await _create_project(client)
    document_id = await _create_document(client)
    await client.post(f"/projects/{project_id}/documents", json={"document_id": document_id})

    response = await client.get(f"/projects/{project_id}/documents")
    body = next(d for d in response.json() if d["id"] == document_id)
    assert body["summarizing"] is False
