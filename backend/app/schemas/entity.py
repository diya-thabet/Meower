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
    phone: Optional[str] = None
    google_id: Optional[str] = None
    social_ids: Optional[list] = None
    profile_urls: Optional[list] = None
    associated_domains: Optional[list] = None
    data_breaches: Optional[list] = None
    services: Optional[list] = None
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


class DomainResponse(BaseModel):
    id: str
    domain: str
    subdomains: Optional[list] = None
    ips: Optional[list] = None
    registrant_email: Optional[str] = None
    technologies: Optional[list] = None
    ssl_info: Optional[dict] = None
    risk_score: int
    first_seen: datetime
    last_seen: datetime


class DomainSummary(BaseModel):
    id: str
    domain: str
    risk_score: int


class EdgeResponse(BaseModel):
    id: str
    source_entity_id: str
    source_type: str
    target_entity_id: str
    target_type: str
    relationship: str
    investigation_id: Optional[str] = None
    first_seen: datetime
