from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    deal_id: UUID
    account_id: UUID
    stripe_payment_id: str
    amount: float
    currency: str = "GBP"
    payment_type: str = "one_time"
    paid_at: Optional[datetime] = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    deal_id: UUID
    account_id: UUID
    stripe_payment_id: str
    amount: float
    currency: str
    payment_type: str
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
