from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    name: str
    slug: str
    meta_ad_account_id: str
    business_type: str
    target_cpl: Optional[float] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    timezone: str = "Europe/London"
    currency: str = "GBP"
    telegram_chat_id: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    meta_ad_account_id: Optional[str] = None
    business_type: Optional[str] = None
    target_cpl: Optional[float] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    telegram_chat_id: Optional[str] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    meta_ad_account_id: str
    business_type: str
    target_cpl: Optional[float] = None
    target_cpa: Optional[float] = None
    target_roas: Optional[float] = None
    timezone: str
    currency: str
    telegram_chat_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
