import pytest
from unittest.mock import patch, AsyncMock
from app.orchestration.pipeline import PipelineBuilder, InvestigationType
from app.orchestration.dispatcher import Dispatcher
from app.tools.base import ToolResult, ToolCategory


@pytest.fixture
def builder():
    return PipelineBuilder()


class TestPipelineBuilder:
    def test_build_email_pipeline(self, builder):
        plan = builder.build("test@example.com", InvestigationType.EMAIL)
        assert plan.seed == "test@example.com"
        assert plan.type == InvestigationType.EMAIL
        assert len(plan.steps) >= 6
        tool_names = [s.tool for s in plan.steps]
        assert "holehe" in tool_names
        assert "ghunt" in tool_names
        assert "h8mail" in tool_names
        assert "sherlock" in tool_names
        assert "maigret" in tool_names

    def test_build_username_pipeline(self, builder):
        plan = builder.build("testuser", InvestigationType.USERNAME)
        assert plan.seed == "testuser"
        tool_names = [s.tool for s in plan.steps]
        assert "sherlock" in tool_names
        assert "maigret" in tool_names
        assert "snscrape" in tool_names

    def test_build_domain_pipeline(self, builder):
        plan = builder.build("example.com", InvestigationType.DOMAIN)
        assert plan.seed == "example.com"
        tool_names = [s.tool for s in plan.steps]
        assert "theHarvester" in tool_names
        assert "emailfinder" in tool_names
        assert "censys" in tool_names or "shodan" in tool_names

    def test_build_unknown_type_defaults_to_email(self, builder):
        plan = builder.build("test@example.com", InvestigationType.PHONE)
        assert "holehe" in [s.tool for s in plan.steps]

    def test_pipeline_step_deps_default_empty(self):
        from app.orchestration.pipeline import PipelineStep
        step = PipelineStep(tool="test", target="x")
        assert step.depends_on == []


class TestDispatcher:
    @pytest.mark.anyio
    async def test_execute_runs_all_tools(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        dispatcher = Dispatcher()

        mock_result = ToolResult(
            tool_name="mock",
            category=ToolCategory.EMAIL,
            status="success",
            raw_data={},
            normalized=[],
        )

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = AsyncMock(return_value=mock_result)
            mock_get_tool.return_value = mock_tool

            results = await dispatcher.execute(plan)

        assert len(results) > 0
        for tool_name, result in results.items():
            assert result.status == "success"

    @pytest.mark.anyio
    async def test_execute_handles_missing_tool(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        dispatcher = Dispatcher()

        with patch("app.orchestration.dispatcher.get_tool", return_value=None):
            results = await dispatcher.execute(plan)

        assert len(results) > 0
        # Some tools may be "missing" and should have error status
        for result in results.values():
            assert result.status in ("success", "error")

    @pytest.mark.anyio
    async def test_execute_handles_exceptions(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        dispatcher = Dispatcher()

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = AsyncMock(side_effect=RuntimeError("boom"))
            mock_get_tool.return_value = mock_tool

            results = await dispatcher.execute(plan)

        assert all(r.status == "error" for r in results.values())

    @pytest.mark.anyio
    async def test_progress_callback_called(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        calls = []

        def callback(tool: str, status: str):
            calls.append((tool, status))

        dispatcher = Dispatcher(progress_callback=callback)

        mock_result = ToolResult(
            tool_name="mock", category=ToolCategory.EMAIL, status="success", raw_data={}
        )

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = AsyncMock(return_value=mock_result)
            mock_get_tool.return_value = mock_tool

            await dispatcher.execute(plan)

        assert len(calls) > 0
        # Each tool should have at least "running" and final status
        call_tools = {c[0] for c in calls}
        for step in plan.steps:
            assert step.tool in call_tools

    @pytest.mark.anyio
    async def test_dispatcher_not_found_in_registry(self):
        from app.orchestration.dispatcher import Dispatcher
        dispatcher = Dispatcher()
        result = await dispatcher._run_step(
            type("Step", (), {"tool": "nonexistent_tool_xyz", "target": "test", "kwargs": {}, "depends_on": []})()
        )
        assert result.status == "error"
        assert "not found" in (result.error or "")
