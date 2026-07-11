from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EntityResponse(BaseModel):
    id: str
    primary_value: str
    type: str
    display_name: str
    risk_score: int
    investigation_count: int
    first_seen: datetime
    last_seen: datetime
    entity_metadata: Optional[dict] = None


class EntitySummary(BaseModel):
    id: str
    primary_value: str
    type: str
    display_name: str
    risk_score: int
    investigation_count: int


class EntitySearchResult(BaseModel):
    results: list[EntitySummary]
    total: int
