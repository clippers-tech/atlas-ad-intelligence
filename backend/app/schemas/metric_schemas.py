from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AdMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    ad_id: Optional[UUID] = None
    spend: Optional[float] = None
    impressions: Optional[int] = None
    clicks: Optional[int] = None
    ctr: Optional[float] = None
    cpc: Optional[float] = None
    cpm: Optional[float] = None
    conversions: Optional[int] = None
    cpl: Optional[float] = None
    cpa: Optional[float] = None
    frequency: Optional[float] = None
    video_view_3s_rate: Optional[float] = None
    video_p25: Optional[float] = None
    video_p50: Optional[float] = None
    video_p75: Optional[float] = None
    video_p100: Optional[float] = None
    reach: Optional[int] = None
    unique_clicks: Optional[int] = None
    timestamp: datetime


class DashboardOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_spend: float
    total_leads: int
    avg_cpl: Optional[float] = None
    avg_cpa: Optional[float] = None
    roas: Optional[float] = None
    active_campaigns: int
    active_ads: int
    date_range: str


class MetricTimeSeriesPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    value: float
