import asyncio
import logging
from typing import Optional, Callable
from .pipeline import PipelinePlan, PipelineStep
from ..tools import get_tool
from ..tools.base import ToolResult

logger = logging.getLogger(__name__)

ProgressCallback = Optional[Callable[[str, str], None]]


class Dispatcher:
    def __init__(self, progress_callback: ProgressCallback = None):
        self.progress_callback = progress_callback

    async def execute(self, plan: PipelinePlan) -> dict[str, ToolResult]:
        results: dict[str, ToolResult] = {}
        steps = plan.steps[:]
        pending = {s.tool for s in steps}

        while pending:
            ready = [s for s in steps if s.tool in pending and self._deps_met(s, results)]
            if not ready:
                logger.warning("Stalled pipeline: remaining=%s", pending)
                break

            tasks = [self._run_step(step) for step in ready]
            outcomes = await asyncio.gather(*tasks, return_exceptions=True)

            for step, outcome in zip(ready, outcomes):
                if isinstance(outcome, Exception):
                    logger.error("Step %s failed: %s", step.tool, outcome)
                    results[step.tool] = ToolResult(
                        tool_name=step.tool,
                        category=None,  # type: ignore
                        status="error",
                        raw_data={},
                        error=str(outcome),
                    )
                else:
                    results[step.tool] = outcome
                pending.discard(step.tool)

        return results

    def _deps_met(self, step: PipelineStep, results: dict) -> bool:
        return all(dep in results for dep in step.depends_on)

    async def _run_step(self, step: PipelineStep) -> ToolResult:
        tool = get_tool(step.tool)
        if tool is None:
            return ToolResult(
                tool_name=step.tool,
                category=None,  # type: ignore
                status="error",
                raw_data={},
                error=f"Tool '{step.tool}' not found in registry",
            )

        if self.progress_callback:
            self.progress_callback(step.tool, "running")

        result = await tool.run(step.target, **step.kwargs)

        if self.progress_callback:
            self.progress_callback(step.tool, result.status)

        return result
