import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ...schemas.entity import (
    EntityResponse, EntitySummary, EntitySearchResult,
    DomainResponse, DomainSummary, EdgeResponse,
)
from ...models.entity import PersonEntity, DomainEntity, EntityEdge
from ...db.session import get_db
from ...graph.resolver import EntityResolver
from ...graph.risk import calculate_risk_score, get_risk_label

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/entities", tags=["entities"])


@router.get("", response_model=EntitySearchResult)
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort: str = Query("risk_score", pattern="^(risk_score|last_seen|investigation_count)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    order_col = getattr(PersonEntity, sort, PersonEntity.risk_score)
    order_fn = order_col.desc if order == "desc" else order_col.asc

    count_result = await db.execute(select(func.count(PersonEntity.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(PersonEntity).order_by(order_fn()).offset(skip).limit(limit)
    )
    entities = result.scalars().all()

    return EntitySearchResult(
        results=[EntitySummary(
            id=e.id,
            primary_value=e.primary_value,
            type=e.type,
            display_name=e.display_name,
            risk_score=e.risk_score,
            investigation_count=e.investigation_count,
        ) for e in entities],
        total=total,
    )


@router.get("/search", response_model=EntitySearchResult)
async def search_entities(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    pattern = f"%{q}%"
    count_result = await db.execute(
        select(func.count(PersonEntity.id)).where(
            PersonEntity.primary_value.ilike(pattern)
            | PersonEntity.display_name.ilike(pattern)
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(PersonEntity)
        .where(PersonEntity.primary_value.ilike(pattern) | PersonEntity.display_name.ilike(pattern))
        .order_by(PersonEntity.risk_score.desc())
        .offset(skip)
        .limit(limit)
    )
    entities = result.scalars().all()

    return EntitySearchResult(
        results=[EntitySummary(
            id=e.id,
            primary_value=e.primary_value,
            type=e.type,
            display_name=e.display_name,
            risk_score=e.risk_score,
            investigation_count=e.investigation_count,
        ) for e in entities],
        total=total,
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PersonEntity).where(PersonEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.get("/{entity_id}/risk")
async def get_entity_risk(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PersonEntity).where(PersonEntity.id == entity_id))
    entity = result.scalar_one_or_none()
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {
        "id": entity.id,
        "primary_value": entity.primary_value,
        "risk_score": entity.risk_score,
        "risk_label": get_risk_label(entity.risk_score),
        "investigation_count": entity.investigation_count,
    }


@router.get("/{entity_id}/edges", response_model=list[EdgeResponse])
async def get_entity_edges(
    entity_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(EntityEdge).where(
            (EntityEdge.source_entity_id == entity_id) | (EntityEdge.target_entity_id == entity_id)
        )
    )
    edges = result.scalars().all()
    return edges


@router.get("/domains", response_model=list[DomainSummary])
async def list_domains(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DomainEntity).order_by(DomainEntity.risk_score.desc()).offset(skip).limit(limit)
    )
    domains = result.scalars().all()
    return [DomainSummary(id=d.id, domain=d.domain, risk_score=d.risk_score) for d in domains]


@router.get("/domains/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DomainEntity).where(DomainEntity.id == domain_id))
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain
