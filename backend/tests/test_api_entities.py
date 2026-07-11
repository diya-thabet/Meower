import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.db.session import engine, async_session
from app.db.base import Base
from app.models.entity import PersonEntity


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        entities = [
            PersonEntity(
                primary_value="alice@example.com",
                type="email",
                display_name="Alice",
                risk_score=80,
                investigation_count=3,
            ),
            PersonEntity(
                primary_value="bob@example.com",
                type="email",
                display_name="Bob",
                risk_score=30,
                investigation_count=1,
            ),
            PersonEntity(
                primary_value="charlie",
                type="username",
                display_name="Charlie Dev",
                risk_score=50,
                investigation_count=2,
            ),
        ]
        for e in entities:
            db.add(e)
        await db.commit()

    yield

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


transport = ASGITransport(app=app)


@pytest.mark.anyio
class TestEntityAPI:
    async def test_list_entities(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3

    async def test_list_entities_sorted_by_risk_desc(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities?sort=risk_score&order=desc")
        data = resp.json()
        scores = [r["risk_score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)

    async def test_list_entities_sorted_by_risk_asc(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities?sort=risk_score&order=asc")
        data = resp.json()
        scores = [r["risk_score"] for r in data["results"]]
        assert scores == sorted(scores)

    async def test_list_entities_pagination(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities?skip=0&limit=2")
        data = resp.json()
        assert len(data["results"]) == 2
        assert data["total"] == 3

    async def test_list_entities_skip(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities?skip=2&limit=10")
        data = resp.json()
        assert len(data["results"]) == 1

    async def test_get_entity_by_id(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            list_resp = await client.get("/api/v1/entities")
            entity_id = list_resp.json()["results"][0]["id"]

            resp = await client.get(f"/api/v1/entities/{entity_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == entity_id
        assert data["primary_value"] is not None

    async def test_get_entity_not_found(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/nonexistent-id")
        assert resp.status_code == 404

    async def test_search_entities(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/search?q=alice")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("alice" in r["primary_value"].lower() for r in data["results"])

    async def test_search_entities_partial_match(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/search?q=bob")
        data = resp.json()
        assert data["total"] >= 1

    async def test_search_entities_no_match(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/search?q=nonexistent")
        data = resp.json()
        assert data["total"] == 0
        assert len(data["results"]) == 0

    async def test_get_entity_risk(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            list_resp = await client.get("/api/v1/entities")
            entity_id = list_resp.json()["results"][0]["id"]

            resp = await client.get(f"/api/v1/entities/{entity_id}/risk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == entity_id
        assert "risk_score" in data
        assert "risk_label" in data
        assert data["risk_label"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    async def test_get_entity_risk_not_found(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/nonexistent/risk")
        assert resp.status_code == 404

    async def test_search_empty_query_returns_422(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/search?q=")
        assert resp.status_code == 422

    async def test_get_entity_edges(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            list_resp = await client.get("/api/v1/entities")
            entity_id = list_resp.json()["results"][0]["id"]

            resp = await client.get(f"/api/v1/entities/{entity_id}/edges")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_get_entity_edges_not_found(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/nonexistent/edges")
        assert resp.status_code == 200
        assert resp.json() == []


class TestDomainAPI(TestEntityAPI):
    async def test_list_domains(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/domains")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_list_domains_with_skip(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/domains?skip=0&limit=5")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_domain_by_id_not_found(self):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/entities/domains/nonexistent")
        assert resp.status_code == 404
