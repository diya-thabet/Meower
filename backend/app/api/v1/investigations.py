from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...schemas.investigation import InvestigationCreate, InvestigationResponse, InvestigationSummary
from ...models.investigation import Investigation
from ...db.session import get_db

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
