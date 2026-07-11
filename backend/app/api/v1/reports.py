from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...db.session import get_db
from ...models.investigation import Investigation
from ...llm.service import llm_service
from ...schemas.investigation import InvestigationResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate/{inv_id}", response_model=InvestigationResponse)
async def generate_report(inv_id: str, db: AsyncSession = Depends(get_db)):
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

    try:
        report = await llm_service.generate_report({"tool_results": inv.tool_results})
        inv.report = report
        await db.commit()
        await db.refresh(inv)
        return inv
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}")


@router.get("/status")
async def report_status():
    return {
        "available": llm_service.available,
        "model": llm_service._model,
        "provider": "Fanar",
    }
