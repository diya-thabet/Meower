from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db.session import get_db
from ...models.investigation import Investigation
from ...llm.service import llm_service

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportResponse(BaseModel):
    report: str
    report_type: str


@router.post("/generate/{inv_id}")
async def generate_report(
    inv_id: str,
    report_type: str = Query("full", pattern="^(full|summary|social|breach|risk|dossier)$"),
    force: bool = Query(False, description="Regenerate even if report already exists"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not inv.tool_results:
        raise HTTPException(status_code=400, detail="No tool results to analyze")

    if not llm_service.available:
        raise HTTPException(
            status_code=400,
            detail="FANAR_API_KEY is not configured. Set it in the backend .env file.",
        )

    if report_type == "full" and inv.report and not force:
        return ReportResponse(report=inv.report, report_type="full")

    try:
        data = {
            "seed": inv.seed,
            "type": inv.type,
            "tool_results": inv.tool_results,
            "graph": inv.graph,
            "risk_signals": inv.graph.get("stats", {}).get("risk_signals", []) if inv.graph else [],
            "entities": [],
        }
        report = await llm_service.generate_report(data, report_type=report_type)
        if report_type == "full":
            inv.report = report
            await db.commit()
        return ReportResponse(report=report, report_type=report_type)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}")


@router.get("/types")
async def report_types():
    return {"types": llm_service.report_types}


@router.get("/status")
async def report_status():
    return {
        "available": llm_service.available,
        "model": llm_service._model,
        "provider": "Fanar",
    }
