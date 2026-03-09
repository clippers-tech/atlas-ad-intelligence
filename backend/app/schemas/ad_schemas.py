from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    ad_set_id: Optional[UUID] = None
    meta_ad_id: str
    name: str
    creative_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ad_type: Optional[str] = None
    review_status: Optional[str] = None
    status: str
    first_active_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
