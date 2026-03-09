from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    meta_campaign_id: str
    name: str
    objective: Optional[str] = None
    status: str
    daily_budget: Optional[float] = None
    lifetime_budget: Optional[float] = None
    created_at: datetime
    updated_at: datetime
