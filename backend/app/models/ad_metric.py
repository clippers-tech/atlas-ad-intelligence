"""AdMetric model — time-series, every 15 min."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class AdMetric(Base):
    __tablename__ = "ad_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ads.id"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    # Core metrics
    spend: Mapped[float] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    cpc: Mapped[float] = mapped_column(Float, default=0.0)
    cpm: Mapped[float] = mapped_column(Float, default=0.0)

    # Conversion metrics
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    cpl: Mapped[float] = mapped_column(Float, default=0.0)
    cpa: Mapped[float] = mapped_column(Float, default=0.0)
    frequency: Mapped[float] = mapped_column(Float, default=0.0)

    # Video metrics
    video_view_3s_rate: Mapped[float] = mapped_column(Float, default=0.0)
    video_p25: Mapped[float] = mapped_column(Float, default=0.0)
    video_p50: Mapped[float] = mapped_column(Float, default=0.0)
    video_p75: Mapped[float] = mapped_column(Float, default=0.0)
    video_p100: Mapped[float] = mapped_column(Float, default=0.0)

    # Reach
    reach: Mapped[int] = mapped_column(Integer, default=0)
    unique_clicks: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ad = relationship("Ad", back_populates="metrics")
