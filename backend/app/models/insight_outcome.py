"""InsightOutcome — track if Claude recommendations worked."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class InsightOutcome(Base):
    __tablename__ = "insight_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claude_insights.id"),
        nullable=False, index=True,
    )
    recommendation_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(
        String(50), default="skipped"
        # implemented, skipped, positive_result, negative_result, neutral
    )
    measured_metric: Mapped[str | None] = mapped_column(String(100), nullable=True)
    measured_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    measured_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    insight = relationship("ClaudeInsight", back_populates="outcomes")
