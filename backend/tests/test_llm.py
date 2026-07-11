import pytest
from unittest.mock import AsyncMock
from app.llm.service import LLMService

SAMPLE_DATA = {
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
