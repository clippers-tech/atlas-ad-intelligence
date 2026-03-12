from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LeadCreate(BaseModel):
    account_id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    source_campaign_id: Optional[str] = None
    source_ad_id: Optional[str] = None
    source_adset_id: Optional[str] = None


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    source_campaign_id: Optional[str] = None
    source_ad_id: Optional[str] = None
    source_adset_id: Optional[str] = None
    stage: Optional[str] = None
    # Meta lead form tracking
    meta_lead_id: Optional[str] = None
    meta_form_id: Optional[str] = None
    meta_ad_id: Optional[str] = None
    meta_created_at: Optional[datetime] = None
    created_at: datetime
    bookings: list[Any] = []
    deals: list[Any] = []


class LeadImportRow(BaseModel):
    email: str
    name: Optional[str] = None
    stage: Optional[str] = None
    revenue: Optional[float] = None
    notes: Optional[str] = None
