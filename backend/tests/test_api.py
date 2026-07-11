import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine
from app.db.base import Base


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


transport = ASGITransport(app=app)


@pytest.mark.anyio
async def test_health():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.anyio
async def test_list_tools():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tools")
    assert resp.status_code == 200
    tools = resp.json()
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert tools[0]["name"]
    assert tools[0]["category"]


@pytest.mark.anyio
async def test_list_categories():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/tools/categories")
    assert resp.status_code == 200
    cats = resp.json()
    assert "email" in cats
    assert "username" in cats
    assert "domain" in cats


@pytest.mark.anyio
async def test_create_investigation():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/investigations",
            json={"seed": "test@example.com", "type": "email"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["seed"] == "test@example.com"
    assert data["type"] == "email"
    assert data["status"] == "pending"
    assert data["id"] is not None
    return data["id"]


@pytest.mark.anyio
async def test_get_investigation():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/investigations",
            json={"seed": "get@example.com", "type": "username"},
        )
        inv_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/investigations/{inv_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == inv_id
    assert data["seed"] == "get@example.com"


@pytest.mark.anyio
async def test_get_investigation_not_found():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/investigations/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_list_investigations():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/v1/investigations",
            json={"seed": "a@example.com", "type": "email"},
        )
        await client.post(
            "/api/v1/investigations",
            json={"seed": "b@example.com", "type": "domain"},
        )

        resp = await client.get("/api/v1/investigations")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.anyio
async def test_delete_investigation():
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/api/v1/investigations",
            json={"seed": "delete@example.com", "type": "email"},
        )
        inv_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/v1/investigations/{inv_id}")
    assert delete_resp.status_code == 204

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        get_resp = await client.get(f"/api/v1/investigations/{inv_id}")
    assert get_resp.status_code == 404
