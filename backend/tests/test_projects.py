from httpx import AsyncClient


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
