from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AudienceTestCreate(BaseModel):
    account_id: UUID
    audience_name: str
    audience_type: str
    targeting_json: Optional[dict[str, Any]] = None


class AudienceTestUpdate(BaseModel):
    status: Optional[str] = None
    kill_reason: Optional[str] = None


class AudienceTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    audience_name: str
    audience_type: str
    targeting_json: Optional[dict[str, Any]] = None
    status: str
    kill_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
