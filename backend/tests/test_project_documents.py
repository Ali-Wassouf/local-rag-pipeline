from httpx import AsyncClient


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
