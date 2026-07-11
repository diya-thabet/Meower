from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class InvestigationCreate(BaseModel):
    seed: str
    type: str = "email"
    tools: Optional[list[str]] = None


class InvestigationProgress(BaseModel):
    step_id: str
    tool: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_ms: int = 0


class InvestigationResponse(BaseModel):
    id: str
    seed: str
    type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    tool_results: Optional[dict] = None
    graph: Optional[dict] = None
    report: Optional[str] = None
    error: Optional[str] = None


class InvestigationSummary(BaseModel):
    id: str
    seed: str
    type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
