from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetitorAdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    competitor_config_id: UUID
    meta_ad_id: Optional[str] = None
    creative_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ad_copy: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class CompetitorConfigCreate(BaseModel):
    account_id: UUID
    competitor_name: str
    meta_page_id: Optional[str] = None
    website_url: Optional[str] = None


class CompetitorConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    competitor_name: str
    meta_page_id: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    ads: list[CompetitorAdResponse] = []
