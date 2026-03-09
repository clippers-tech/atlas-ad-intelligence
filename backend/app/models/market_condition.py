"""MarketCondition — BTC price tracking for Web3 account."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class MarketCondition(Base):
    __tablename__ = "market_conditions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    btc_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    btc_7d_change_percent: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    is_btc_crash: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
