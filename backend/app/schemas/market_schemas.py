from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MarketConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: datetime
    btc_price: Optional[float] = None
    btc_7d_change_percent: Optional[float] = None
    is_btc_crash: bool = False
    notes: Optional[str] = None
    created_at: datetime
