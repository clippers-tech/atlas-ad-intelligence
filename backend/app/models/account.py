"""Account model — multi-business support."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    meta_ad_account_id: Mapped[str] = mapped_column(String(100), nullable=False)
    business_type: Mapped[str] = mapped_column(
        String(50), nullable=False  # web3, clippers, agency
    )
    target_cpl: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_cpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_roas: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/London")
    currency: Mapped[str] = mapped_column(String(10), default="GBP")
    meta_page_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    meta_page_token: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    campaigns = relationship("Campaign", back_populates="account", lazy="selectin")
