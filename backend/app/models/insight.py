"""Insight model — AI-generated insights from Computer analysis."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"),
        nullable=True, index=True,
    )
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general"
        # general, performance, creative, audience, budget, anomaly
    )
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    priority: Mapped[str] = mapped_column(
        String(20), default="medium"
        # critical, high, medium, low
    )
    source: Mapped[str | None] = mapped_column(
        String(50), default="computer"
        # computer_schedule, manual
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
