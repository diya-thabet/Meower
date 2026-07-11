import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from ..models.investigation import Investigation
from ..db.session import async_session
from .pipeline import InvestigationType, PipelineBuilder
from .dispatcher import Dispatcher
from ..graph.builder import GraphBuilder
from ..llm.service import llm_service
from ..ws.manager import ws_manager

logger = logging.getLogger(__name__)


class InvestigationRunner:
    def __init__(self):
        self._running: set[str] = set()

    async def run(self, investigation_id: str, seed: str, inv_type: str) -> None:
        if investigation_id in self._running:
            logger.warning("Investigation %s is already running", investigation_id)
            return
        self._running.add(investigation_id)

        try:
            inv_type_enum = InvestigationType(inv_type)
        except ValueError:
            await self._update_db(investigation_id, status="failed", error=f"Invalid investigation type: {inv_type}")
            await ws_manager.broadcast(investigation_id, {"type": "status", "status": "failed", "error": f"Invalid type: {inv_type}"})
            self._running.discard(investigation_id)
            return

        builder = PipelineBuilder()
        plan = builder.build(seed, inv_type_enum)

        async def progress_callback(tool: str, status: str):
            await ws_manager.broadcast(
                investigation_id,
                {"type": "tool_progress", "tool": tool, "status": status},
            )

        dispatcher = Dispatcher(progress_callback=progress_callback)

        try:
            await ws_manager.broadcast(investigation_id, {"type": "status", "status": "running"})

            results = await dispatcher.execute(plan)

            merged = self._merge_results(results)

            graph_builder = GraphBuilder()
            graph = graph_builder.build(seed, merged)

            report = None
            if llm_service.available:
                try:
                    await ws_manager.broadcast(investigation_id, {"type": "status", "status": "generating_report"})
                    report = await llm_service.generate_report(seed, merged)
                except Exception as e:
                    logger.error("Report generation failed: %s", e)
                    report = f"[Report generation failed: {e}]"

            now = datetime.now(timezone.utc)
            await self._update_db(
                investigation_id,
                status="completed",
                completed_at=now,
                tool_results=merged,
                graph=graph,
                report=report,
                error=None,
            )

            await self._resolve_entities(investigation_id, seed, inv_type, merged, graph)

            await ws_manager.broadcast(investigation_id, {"type": "status", "status": "completed"})

        except Exception as e:
            logger.exception("Investigation %s failed", investigation_id)
            await self._update_db(
                investigation_id,
                status="failed",
                error=str(e),
            )
            await ws_manager.broadcast(investigation_id, {"type": "status", "status": "failed", "error": str(e)})
        finally:
            self._running.discard(investigation_id)

    def _merge_results(self, results: dict[str, Any]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for tool, result in results.items():
            if result is None:
                continue
            if hasattr(result, "to_dict"):
                merged[tool] = result.to_dict()
            elif isinstance(result, dict):
                merged[tool] = result
            else:
                merged[tool] = str(result)
        return merged

    async def _resolve_entities(self, investigation_id: str, seed: str, inv_type: str, merged: dict, graph: dict) -> None:
        try:
            from ..graph.resolver import EntityResolver
            from ..graph.risk import calculate_risk_score
            risk_score = calculate_risk_score(seed, merged)
            resolver = EntityResolver()
            entities = await resolver.resolve_from_investigation(
                seed, inv_type, merged, risk_score,
                investigation_id=investigation_id,
            )
            if entities:
                logger.info("Resolved %d entities from investigation", len(entities))
        except Exception as e:
            logger.error("Entity resolution failed: %s", e)

    async def _update_db(self, investigation_id: str, **kwargs) -> None:
        async with async_session() as db:
            result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
            inv = result.scalar_one_or_none()
            if inv is None:
                logger.error("Investigation %s not found in DB", investigation_id)
                return
            for key, val in kwargs.items():
                setattr(inv, key, val)
            await db.commit()


investigation_runner = InvestigationRunner()
