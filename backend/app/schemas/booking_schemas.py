from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    lead_id: UUID
    account_id: UUID
    calendly_event_id: str
    event_type: Optional[str] = None
    status: str = "scheduled"
    booked_at: Optional[datetime] = None
    event_at: Optional[datetime] = None


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    account_id: UUID
    calendly_event_id: str
    event_type: Optional[str] = None
    status: str
    booked_at: Optional[datetime] = None
    event_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
