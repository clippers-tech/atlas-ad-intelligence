"""Schemas for competitor config, ad ingest, and summary responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetitorAdResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    competitor_config_id: UUID
    creative_url: Optional[str] = None
    ad_text: Optional[str] = None
    hook_text: Optional[str] = None
    estimated_spend_range: Optional[str] = None
    impression_range: Optional[str] = None
    hook_type: Optional[str] = None
    cta_type: Optional[str] = None
    offer_text: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_active: bool = True
    ai_analysis_json: Optional[str] = None
    created_at: datetime


class CompetitorConfigCreate(BaseModel):
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
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class CompetitorAdIngest(BaseModel):
    """Single ad record from external source (Ad Library)."""
    creative_url: Optional[str] = None
    ad_text: Optional[str] = None
    hook_text: Optional[str] = None
    estimated_spend_range: Optional[str] = None
    impression_range: Optional[str] = None
    hook_type: Optional[str] = None
    cta_type: Optional[str] = None
    offer_text: Optional[str] = None


class CompetitorAdsIngestRequest(BaseModel):
    """Batch ingest request for competitor ads."""
    competitor_config_id: UUID
    ads: list[CompetitorAdIngest]


class CompetitorSummaryResponse(BaseModel):
    """Per-competitor summary stats."""
    competitor_config_id: str
    competitor_name: str
    meta_page_id: Optional[str] = None
    website_url: Optional[str] = None
    is_active: bool = True
    total_ads: int = 0
    active_ads: int = 0
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
