"""AdSet model with audience_type + optimization_event."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class AdSet(Base):
    __tablename__ = "ad_sets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"),
        nullable=False, index=True,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"),
        nullable=False, index=True,
    )
    meta_adset_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    audience_type: Mapped[str] = mapped_column(
        String(50), default="broad"
    )
    targeting_json: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    daily_budget: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="ACTIVE"
    )
    # Meta optimization event, e.g.
    # "offsite_conversion.custom.3284105835088992"
    optimization_event: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(),
    )

    campaign = relationship(
        "Campaign", back_populates="ad_sets"
    )
    ads = relationship(
        "Ad", back_populates="ad_set", lazy="selectin"
    )
