"""Ad model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True
    )
    ad_set_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ad_sets.id"), nullable=False, index=True
    )
    meta_ad_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    creative_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    ad_type: Mapped[str] = mapped_column(
        String(50), default="image"  # image, video, carousel
    )
    review_status: Mapped[str] = mapped_column(
        String(50), default="approved"
        # approved, disapproved, pending, in_review
    )
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    first_active_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ad_set = relationship("AdSet", back_populates="ads")
    metrics = relationship("AdMetric", back_populates="ad", lazy="selectin")
    creative_metadata = relationship(
        "CreativeMetadata", back_populates="ad", uselist=False, lazy="selectin"
    )
