from httpx import AsyncClient


async def test_get_job_after_upload(client: AsyncClient) -> None:
    upload = await client.post(
        "/documents", files={"file": ("notes.md", b"# hi", "text/markdown")}
    )
    job_id = upload.json()["job_id"]

    response = await client.get(f"/jobs/{job_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == job_id
    assert body["stage"] == "extract"
    assert body["progress"] == 0


async def test_get_job_not_found(client: AsyncClient) -> None:
    response = await client.get("/jobs/999999")
    assert response.status_code == 404
