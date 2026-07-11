import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from app.tools._runner import run_cli, _make_result
from app.tools.base import ToolCategory


@pytest.mark.anyio
async def test_run_cli_success():
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"output data", b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        result = await run_cli("test_tool", ToolCategory.EMAIL, ["echo", "hello"])

    assert result.tool_name == "test_tool"
    assert result.category == ToolCategory.EMAIL
    assert result.status == "success"
    assert "output data" in result.raw_data.get("stdout", "")


@pytest.mark.anyio
async def test_run_cli_nonzero_exit():
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"", b"error message"))
    mock_proc.returncode = 1

    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        result = await run_cli("test_tool", ToolCategory.USERNAME, ["false"])

    assert result.status == "error"
    assert "error message" in (result.error or "")


@pytest.mark.anyio
async def test_run_cli_timeout():
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_proc.kill = AsyncMock()
    mock_proc.wait = AsyncMock()

    with patch("asyncio.create_subprocess_exec", AsyncMock(return_value=mock_proc)):
        result = await run_cli("test_tool", ToolCategory.DOMAIN, ["sleep", "999"], timeout=1)

    assert result.status == "error"
    assert result.error == "Timed out"


@pytest.mark.anyio
async def test_run_cli_not_found():
    result = await run_cli("missing_tool", ToolCategory.EMAIL, ["nonexistent_command_xyz"])

    assert result.status == "error"
    assert "not found" in (result.error or "")


@pytest.mark.anyio
async def test_make_result_defaults():
    result = _make_result("tool", ToolCategory.EMAIL, "success")
    assert result.tool_name == "tool"
    assert result.status == "success"
    assert result.raw_data == {}
    assert result.normalized == []
    assert result.error is None
    assert result.duration_ms == 0


@pytest.mark.anyio
async def test_make_result_with_data():
    result = _make_result(
        "tool", ToolCategory.SOCIAL, "error",
        raw_data={"key": "val"},
        normalized=[{"id": 1}],
        error="something broke",
        duration_ms=500,
    )
    assert result.raw_data == {"key": "val"}
    assert result.normalized == [{"id": 1}]
    assert result.error == "something broke"
    assert result.duration_ms == 500
