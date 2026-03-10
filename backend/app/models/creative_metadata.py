"""CreativeMetadata — hook_type, cta_type, video_length, etc."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class CreativeMetadata(Base):
    __tablename__ = "creative_metadata"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ad_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ads.id"), nullable=False, unique=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )

    hook_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
        # question, statistic, pain_point, testimonial, shock, story
    )
    cta_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True
        # book_call, learn_more, sign_up, get_quote, watch_more
    )
    video_length_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str | None] = mapped_column(
        String(50), nullable=True
        # ugc, talking_head, motion_graphics, slideshow
    )
    first_active_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_fatigued: Mapped[bool] = mapped_column(Boolean, default=False)
    fatigued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    auto_tagged_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_analysis_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ad = relationship("Ad", back_populates="creative_metadata")
