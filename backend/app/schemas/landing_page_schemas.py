from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LandingPageEventCreate(BaseModel):
    account_id: UUID
    page_url: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    scroll_depth_percent: Optional[float] = None
    time_on_page_seconds: Optional[int] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None


class LandingPageEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    page_url: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    scroll_depth_percent: Optional[float] = None
    time_on_page_seconds: Optional[int] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    created_at: datetime
