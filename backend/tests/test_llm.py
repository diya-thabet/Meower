import pytest
from unittest.mock import AsyncMock
from app.llm.service import LLMService

SAMPLE_DATA = {
    "seed": "test@example.com",
    "type": "email",
    "tool_results": {
        "holehe": {
            "status": "success",
            "normalized": [
                {"service": "twitter", "exists": True, "email": "test@example.com"},
                {"service": "github", "exists": True, "email": "test@example.com"},
            ],
        },
        "sherlock": {
            "status": "success",
            "normalized": [
                {"site": "github", "url": "https://github.com/testuser", "username": "testuser"},
            ],
        },
    },
    "graph": {
        "nodes": [{"data": {"id": "seed", "label": "test@example.com", "type": "email"}}],
        "edges": [],
        "stats": {"risk_score": 30, "risk_label": "MEDIUM", "risk_signals": ["data_breach"]},
    },
}


@pytest.mark.anyio
async def test_llm_service_available():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock report content")
    result = await service.generate_report(SAMPLE_DATA)
    assert "Mock report content" in result
    service._call.assert_awaited_once()


@pytest.mark.anyio
async def test_llm_service_build_context():
    service = LLMService()
    context = service._build_context(SAMPLE_DATA)
    assert "holehe" in context
    assert "sherlock" in context
    assert "twitter" in context
    assert "github" in context
    assert "test@example.com" in context
    assert "Risk Score: 30" in context


@pytest.mark.anyio
async def test_llm_service_build_context_empty():
    service = LLMService()
    context = service._build_context({})
    assert context == "No data collected."


@pytest.mark.anyio
async def test_llm_service_raises_without_key():
    service = LLMService()
    service._client = None
    with pytest.raises(RuntimeError, match="FANAR_API_KEY"):
        _ = service.client


@pytest.mark.anyio
async def test_report_types():
    service = LLMService()
    types = service.report_types
    ids = [t["id"] for t in types]
    assert "full" in ids
    assert "summary" in ids
    assert "social" in ids
    assert "breach" in ids
    assert "risk" in ids
    assert "dossier" in ids


@pytest.mark.anyio
async def test_generate_summary():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock summary")
    result = await service.generate_summary(SAMPLE_DATA)
    assert result == "Mock summary"


@pytest.mark.anyio
async def test_generate_social_profile():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock social profile")
    result = await service.generate_social_profile(SAMPLE_DATA)
    assert result == "Mock social profile"


@pytest.mark.anyio
async def test_generate_breach_analysis():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock breach analysis")
    result = await service.generate_breach_analysis(SAMPLE_DATA)
    assert result == "Mock breach analysis"


@pytest.mark.anyio
async def test_generate_risk_assessment():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock risk assessment")
    result = await service.generate_risk_assessment(SAMPLE_DATA)
    assert result == "Mock risk assessment"


@pytest.mark.anyio
async def test_generate_dossier():
    service = LLMService()
    service._call = AsyncMock(return_value="Mock dossier")
    result = await service.generate_dossier(SAMPLE_DATA)
    assert result == "Mock dossier"
