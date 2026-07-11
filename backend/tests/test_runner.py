import pytest
from unittest.mock import AsyncMock, patch, PropertyMock

from app.orchestration.runner import InvestigationRunner
from app.orchestration.pipeline import PipelinePlan, InvestigationType


@pytest.fixture
def runner():
    return InvestigationRunner()


class TestRunnerMerge:
    def test_merge_skips_none_in_dict(self, runner):
        merged = runner._merge_results({"tool1": None})
        assert merged == {}

    def test_merge_toolresult_with_to_dict(self, runner):
        class FakeResult:
            def to_dict(self):
                return {"name": "test", "status": "success"}

        merged = runner._merge_results({"tool": FakeResult()})
        assert merged == {"tool": {"name": "test", "status": "success"}}

    def test_merge_dict_result(self, runner):
        merged = runner._merge_results({"tool": {"status": "success", "data": []}})
        assert merged == {"tool": {"status": "success", "data": []}}

    def test_merge_string_result(self, runner):
        merged = runner._merge_results({"tool": "some_string"})
        assert merged == {"tool": "some_string"}

    def test_merge_multiple_tools(self, runner):
        results = {
            "holehe": {"status": "success", "normalized": [{"service": "github"}]},
            "sherlock": {"status": "error", "error": "not found"},
        }
        merged = runner._merge_results(results)
        assert len(merged) == 2
        assert merged["holehe"]["normalized"][0]["service"] == "github"


@pytest.mark.anyio
class TestRunnerDedup:
    async def test_does_not_start_running_twice(self, runner):
        runner._running.add("inv-1")
        with patch.object(runner, "_update_db") as mock_update:
            await runner.run("inv-1", "test@example.com", "email")
            mock_update.assert_not_called()

    async def test_rejects_invalid_type(self, runner):
        with (
            patch.object(runner, "_update_db") as mock_update,
            patch("app.orchestration.runner.ws_manager.broadcast") as mock_broadcast,
        ):
            mock_update.return_value = None
            mock_broadcast.return_value = None
            await runner.run("inv-2", "test", "invalid_type")
            assert "inv-2" not in runner._running
            mock_update.assert_awaited_once()


@pytest.mark.anyio
class TestRunnerEdgeCases:
    async def test_empty_seed(self, runner):
        mock_plan = PipelinePlan(seed="", type=InvestigationType.EMAIL, steps=[])
        with (
            patch.object(runner, "_update_db") as mock_update,
            patch("app.orchestration.runner.ws_manager.broadcast") as _,
            patch("app.orchestration.runner.PipelineBuilder.build", return_value=mock_plan),
            patch("app.orchestration.runner.Dispatcher") as mock_dispatcher_cls,
        ):
            mock_dispatcher = AsyncMock()
            mock_dispatcher_cls.return_value = mock_dispatcher
            mock_dispatcher.execute.return_value = {}

            await runner.run("inv-empty", "", "email")
            assert "inv-empty" not in runner._running
            mock_update.assert_awaited_once()

    async def test_all_tools_fail(self, runner):
        mock_plan = PipelinePlan(seed="test@example.com", type=InvestigationType.EMAIL, steps=[])
        with (
            patch.object(runner, "_update_db") as mock_update,
            patch("app.orchestration.runner.ws_manager.broadcast") as _,
            patch("app.orchestration.runner.PipelineBuilder.build", return_value=mock_plan),
            patch("app.orchestration.runner.Dispatcher") as mock_dispatcher_cls,
        ):
            mock_dispatcher = AsyncMock()
            mock_dispatcher_cls.return_value = mock_dispatcher
            mock_dispatcher.execute.side_effect = RuntimeError("All tools crashed")

            await runner.run("inv-fail", "test@example.com", "email")
            assert "inv-fail" not in runner._running
            mock_update.assert_awaited_once()

    async def test_run_cleans_up_running_set_on_failure(self, runner):
        mock_plan = PipelinePlan(seed="test", type=InvestigationType.EMAIL, steps=[])
        with (
            patch.object(runner, "_update_db") as mock_update,
            patch("app.orchestration.runner.ws_manager.broadcast") as _,
            patch("app.orchestration.runner.PipelineBuilder.build", return_value=mock_plan),
        ):
            mock_update.side_effect = Exception("DB error")

            with pytest.raises(Exception, match="DB error"):
                await runner.run("inv-cleanup", "test", "email")
            assert "inv-cleanup" not in runner._running

    async def test_report_generation_failure_does_not_crash(self, runner):
        mock_plan = PipelinePlan(seed="test", type=InvestigationType.EMAIL, steps=[])
        with (
            patch.object(runner, "_update_db") as mock_update,
            patch("app.orchestration.runner.ws_manager.broadcast") as _,
            patch("app.orchestration.runner.PipelineBuilder.build", return_value=mock_plan),
            patch("app.orchestration.runner.Dispatcher") as mock_dispatcher_cls,
            patch("app.orchestration.runner.llm_service") as mock_llm,
        ):
            mock_dispatcher = AsyncMock()
            mock_dispatcher_cls.return_value = mock_dispatcher
            mock_dispatcher.execute.return_value = {"holehe": {"status": "error"}}

            type(mock_llm).available = PropertyMock(return_value=True)
            mock_llm.generate_report = AsyncMock(side_effect=Exception("LLM unavailable"))

            await runner.run("inv-rep", "test", "email")
            assert "inv-rep" not in runner._running
            mock_update.assert_awaited_once()
