"""Lead model — attribution tracking, NOT a CRM."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"),
        nullable=False, index=True,
    )
    source_campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id"), nullable=True
    )
    source_ad_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ads.id"), nullable=True
    )
    source_adset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ad_sets.id"), nullable=True
    )

    # Meta lead form dedup key
    meta_lead_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    meta_form_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    meta_ad_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    # Pipeline stage
    stage: Mapped[str] = mapped_column(
        String(50), default="new"
        # new, contacted, qualified, proposal, closed_won, closed_lost
    )

    # UTM tracking
    utm_campaign: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    utm_source: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    utm_medium: Mapped[str | None] = mapped_column(
        String(200), nullable=True
    )
    utm_content: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    utm_term: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # Contact info
    email: Mapped[str | None] = mapped_column(
        String(320), nullable=True, index=True
    )
    name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    # When the lead was captured on Meta's side
    meta_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    bookings = relationship(
        "Booking", back_populates="lead", lazy="selectin"
    )
    deals = relationship(
        "Deal", back_populates="lead", lazy="selectin"
    )
