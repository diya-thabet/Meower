import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from ..db.base import Base


class PersonEntity(Base):
    __tablename__ = "entities"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    primary_value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(512), default="")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    investigation_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    social_ids: Mapped[Optional[dict]] = mapped_column("social_ids", JSON, nullable=True)
    profile_urls: Mapped[Optional[list]] = mapped_column("profile_urls", JSON, nullable=True)
    associated_domains: Mapped[Optional[list]] = mapped_column("associated_domains", JSON, nullable=True)
    data_breaches: Mapped[Optional[list]] = mapped_column("data_breaches", JSON, nullable=True)
    services: Mapped[Optional[list]] = mapped_column("services", JSON, nullable=True)
    entity_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.entity_metadata is None:
            self.entity_metadata = {}


class DomainEntity(Base):
    __tablename__ = "domains"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    domain: Mapped[str] = mapped_column(String(512), nullable=False, unique=True, index=True)
    subdomains: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ips: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    registrant_email: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    technologies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    ssl_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.id is None:
            self.id = str(uuid.uuid4())


class EntityEdge(Base):
    __tablename__ = "entity_edges"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(16), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)
    relationship: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    investigation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    edge_metadata: Mapped[Optional[dict]] = mapped_column("edge_metadata", JSON, nullable=True)

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.id is None:
            self.id = str(uuid.uuid4())
