"""CompetitorAd model — scraped competitor creatives."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class CompetitorAd(Base):
    __tablename__ = "competitor_ads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    competitor_config_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("competitor_configs.id"),
        nullable=False, index=True,
    )

    creative_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    ad_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    hook_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_spend_range: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    impression_range: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    hook_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cta_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    offer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_seen: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    claude_analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    config = relationship("CompetitorConfig", back_populates="ads")
