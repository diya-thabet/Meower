import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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

    def test_email_pipeline_domain_extraction(self, builder):
        plan = builder.build("user@domain.com", InvestigationType.EMAIL)
        theharvester = [s for s in plan.steps if s.tool == "theHarvester"]
        assert len(theharvester) == 1
        assert theharvester[0].target == "domain.com"

    def test_email_pipeline_username_extraction(self, builder):
        plan = builder.build("john.doe@example.com", InvestigationType.EMAIL)
        sherlock = [s for s in plan.steps if s.tool == "sherlock"]
        assert len(sherlock) == 1
        assert sherlock[0].target == "john.doe"

    def test_empty_seed_email_pipeline(self, builder):
        plan = builder.build("", InvestigationType.EMAIL)
        assert plan.seed == ""
        assert len(plan.steps) > 0

    def test_special_chars_in_seed(self, builder):
        plan = builder.build("user+tag@example.com", InvestigationType.EMAIL)
        assert plan.seed == "user+tag@example.com"

    def test_build_pipeline_all_types(self, builder):
        for t in InvestigationType:
            plan = builder.build("test", t)
            assert len(plan.steps) >= 1


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
        call_tools = {c[0] for c in calls}
        for step in plan.steps:
            assert step.tool in call_tools

    @pytest.mark.anyio
    async def test_dispatcher_not_found_in_registry(self):
        dispatcher = Dispatcher()
        step_mock = MagicMock()
        step_mock.tool = "nonexistent_tool_xyz"
        step_mock.target = "test"
        step_mock.kwargs = {}
        step_mock.depends_on = []
        result = await dispatcher._run_step(step_mock)
        assert result.status == "error"
        assert "not found" in (result.error or "")

    @pytest.mark.anyio
    async def test_mixed_tool_results(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        dispatcher = Dispatcher()

        results_map: dict[str, ToolResult] = {
            "holehe": ToolResult(tool_name="holehe", category=ToolCategory.EMAIL, status="success", raw_data={}),
            "ghunt": ToolResult(tool_name="ghunt", category=ToolCategory.EMAIL, status="error", raw_data={}, error="rate limited"),
        }

        async def mock_run(target: str, **kwargs):
            return results_map.get(kwargs.get("tool_name", target) if "tool_name" in kwargs else target,
                                    ToolResult(tool_name="mock", category=ToolCategory.EMAIL, status="success", raw_data={}))

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = mock_run
            mock_get_tool.return_value = mock_tool

            results = await dispatcher.execute(plan)

        statuses = set(r.status for r in results.values())
        assert "success" in statuses

    @pytest.mark.anyio
    async def test_async_progress_callback(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        calls = []

        async def async_callback(tool: str, status: str):
            calls.append((tool, status))

        dispatcher = Dispatcher(progress_callback=async_callback)

        mock_result = ToolResult(
            tool_name="mock", category=ToolCategory.EMAIL, status="success", raw_data={}
        )

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = AsyncMock(return_value=mock_result)
            mock_get_tool.return_value = mock_tool

            await dispatcher.execute(plan)

        assert len(calls) > 0

    @pytest.mark.anyio
    async def test_stalled_pipeline_returns_partial(self):
        plan = PipelineBuilder().build("test@example.com", InvestigationType.EMAIL)
        for step in plan.steps:
            step.depends_on = ["never_gonna_happen"]
        dispatcher = Dispatcher()

        results = await dispatcher.execute(plan)
        assert len(results) == 0

    @pytest.mark.anyio
    async def test_empty_pipeline(self):
        from app.orchestration.pipeline import PipelinePlan
        plan = PipelinePlan(seed="test", type=InvestigationType.EMAIL, steps=[])
        dispatcher = Dispatcher()
        results = await dispatcher.execute(plan)
        assert results == {}


class TestRunner:
    @pytest.mark.anyio
    async def test_runner_invalid_type(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        mock_ws = AsyncMock()
        with patch.object(runner, "_update_db", AsyncMock()) as mock_update:
            with patch("app.orchestration.runner.ws_manager", mock_ws):
                await runner.run("test-id", "seed", "invalid_type")
        mock_update.assert_called_once()
        args, kwargs = mock_update.call_args
        assert kwargs.get("status") == "failed"
        assert "Invalid investigation type" in kwargs.get("error", "")
        assert "test-id" not in runner._running

    @pytest.mark.anyio
    async def test_runner_dedup(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        runner._running.add("dup-id")
        mock_ws = AsyncMock()
        with patch.object(runner, "_update_db", AsyncMock()):
            with patch("app.orchestration.runner.ws_manager", mock_ws):
                await runner.run("dup-id", "seed", "email")
        assert "dup-id" in runner._running

    @pytest.mark.anyio
    async def test_merge_results_none(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        merged = runner._merge_results({"tool1": None})
        assert merged == {}

    @pytest.mark.anyio
    async def test_merge_results_with_attrs(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()

        class FakeResult:
            def to_dict(self):
                return {"key": "value"}

        merged = runner._merge_results({"tool1": FakeResult()})
        assert merged["tool1"] == {"key": "value"}

    @pytest.mark.anyio
    async def test_merge_results_dict(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        merged = runner._merge_results({"tool1": {"a": 1}})
        assert merged["tool1"] == {"a": 1}

    @pytest.mark.anyio
    async def test_merge_results_string_fallback(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        merged = runner._merge_results({"tool1": 42})
        assert merged["tool1"] == "42"

    @pytest.mark.anyio
    async def test_runner_db_not_found_logs_error(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        with patch("app.orchestration.runner.async_session") as mock_session:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_conn = AsyncMock()
            mock_conn.execute = AsyncMock(return_value=mock_result)
            mock_session.return_value.__aenter__.return_value = mock_conn
            await runner._update_db("nonexistent-id", status="completed")
        mock_conn.execute.assert_called_once()

    @pytest.mark.anyio
    async def test_resolve_entities_empty_doesnt_crash(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()
        await runner._resolve_entities("inv-id", "seed", "email", {}, {"nodes": [], "edges": []})

    @pytest.mark.anyio
    async def test_run_success_path(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()

        mock_ws = AsyncMock()
        mock_llm = AsyncMock()
        mock_llm.available = True
        mock_llm.generate_report = AsyncMock(return_value="Test report")
        mock_result = ToolResult(
            tool_name="mock", category=ToolCategory.EMAIL, status="success", raw_data={}
        )

        async def mock_run(target: str, **kw):
            return mock_result

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = mock_run
            mock_get_tool.return_value = mock_tool
            with patch.object(runner, "_update_db", AsyncMock()):
                with patch("app.orchestration.runner.ws_manager", mock_ws):
                    with patch("app.orchestration.runner.llm_service", mock_llm):
                        with patch.object(runner, "_resolve_entities", AsyncMock()):
                            await runner.run("success-id", "test@example.com", "email")

        assert "success-id" not in runner._running

    @pytest.mark.anyio
    async def test_run_with_report_generation_failure(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()

        mock_ws = AsyncMock()
        mock_llm = AsyncMock()
        mock_llm.available = True
        mock_llm.generate_report = AsyncMock(side_effect=ValueError("LLM error"))
        mock_result = ToolResult(
            tool_name="mock", category=ToolCategory.EMAIL, status="success", raw_data={}
        )

        async def mock_run(target: str, **kw):
            return mock_result

        with patch("app.orchestration.dispatcher.get_tool") as mock_get_tool:
            mock_tool = AsyncMock()
            mock_tool.run = mock_run
            mock_get_tool.return_value = mock_tool
            with patch.object(runner, "_update_db", AsyncMock()):
                with patch("app.orchestration.runner.ws_manager", mock_ws):
                    with patch("app.orchestration.runner.llm_service", mock_llm):
                        with patch.object(runner, "_resolve_entities", AsyncMock()):
                            await runner.run("report-fail-id", "test@example.com", "email")

        assert "report-fail-id" not in runner._running

    @pytest.mark.anyio
    async def test_run_with_dispatcher_exception_caught(self):
        from app.orchestration.runner import InvestigationRunner
        runner = InvestigationRunner()

        mock_ws = AsyncMock()
        with patch.object(runner, "_update_db", AsyncMock()):
            with patch("app.orchestration.runner.ws_manager", mock_ws):
                with patch("app.orchestration.runner.Dispatcher") as mock_disp:
                    mock_disp.return_value.execute.side_effect = RuntimeError("dispatch error")
                    await runner.run("crash-id", "test@example.com", "email")

        assert "crash-id" not in runner._running
