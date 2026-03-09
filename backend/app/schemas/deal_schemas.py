from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DealCreate(BaseModel):
    lead_id: UUID
    account_id: UUID
    stage: str = "new"


class DealUpdate(BaseModel):
    stage: Optional[str] = None
    revenue: Optional[float] = None
    proposal_sent_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None


class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    account_id: UUID
    stage: str
    revenue: Optional[float] = None
    proposal_sent_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    payments: list[Any] = []
