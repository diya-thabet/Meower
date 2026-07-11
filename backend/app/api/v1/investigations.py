import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ...schemas.investigation import InvestigationCreate, InvestigationResponse, InvestigationSummary
from ...models.investigation import Investigation
from ...db.session import get_db
from ...orchestration.runner import investigation_runner
from ...ws.manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationResponse, status_code=201)
async def create_investigation(
    body: InvestigationCreate,
    db: AsyncSession = Depends(get_db),
):
    inv = Investigation(seed=body.seed, type=body.type)
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    asyncio.ensure_future(
        investigation_runner.run(
            investigation_id=inv.id,
            seed=inv.seed,
            inv_type=inv.type,
        )
    )

    return inv


@router.get("", response_model=list[InvestigationSummary])
async def list_investigations(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Investigation).order_by(Investigation.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.get("/{inv_id}", response_model=InvestigationResponse)
async def get_investigation(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.delete("/{inv_id}", status_code=204)
async def delete_investigation(
    inv_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    await db.delete(inv)
    await db.commit()


@router.websocket("/ws/{inv_id}")
async def investigation_ws(
    ws: WebSocket,
    inv_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == inv_id))
    inv = result.scalar_one_or_none()
    if not inv:
        await ws.close(code=4004, reason="Investigation not found")
        return

    await ws_manager.connect(inv_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WebSocket error for %s: %s", inv_id, e)
    finally:
        ws_manager.disconnect(inv_id, ws)
