from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.document import Document


async def test_upload_returns_job_and_creates_document(client: AsyncClient) -> None:
    response = await client.post(
        "/documents",
        files={"file": ("report.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["deduped"] is False
    assert body["job_id"] is not None
    assert body["document"]["title"] == "report"
    assert body["document"]["format"] == "txt"


async def test_uploading_same_content_twice_dedupes(
    client: AsyncClient, db_session
) -> None:
    content = b"the quick brown fox"
    first = await client.post(
        "/documents", files={"file": ("a.txt", content, "text/plain")}
    )
    second = await client.post(
        "/documents", files={"file": ("b.txt", content, "text/plain")}
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["deduped"] is False
    assert second.json()["deduped"] is True
    assert second.json()["job_id"] is None
    assert first.json()["document"]["id"] == second.json()["document"]["id"]

    sha256 = first.json()["document"]["sha256"]
    count = await db_session.scalar(
        select(func.count()).select_from(Document).where(Document.sha256 == sha256)
    )
    assert count == 1


async def test_upload_rejects_unsupported_format(client: AsyncClient) -> None:
    response = await client.post(
        "/documents", files={"file": ("data.exe", b"binary", "application/octet-stream")}
    )
    assert response.status_code == 400


async def test_get_document_not_found(client: AsyncClient) -> None:
    response = await client.get("/documents/999999")
    assert response.status_code == 404


async def test_list_all_documents(client: AsyncClient) -> None:
    await client.post("/documents", files={"file": ("x.txt", b"content x", "text/plain")})
    response = await client.get("/documents")
    assert response.status_code == 200
    titles = [d["title"] for d in response.json()]
    assert "x" in titles
