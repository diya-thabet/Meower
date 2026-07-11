import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from ..db.base import Base


class PersonEntity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    primary_value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(512), default="")
    risk_score: Mapped[int] = mapped_column(Integer, default=0)
    investigation_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    entity_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, default=dict)
