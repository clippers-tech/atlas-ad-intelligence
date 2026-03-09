from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    ad_id: Optional[UUID] = None
    rule_id: Optional[UUID] = None
    action_type: str
    details_json: Optional[dict[str, Any]] = None
    is_reversible: bool
    reversed_at: Optional[datetime] = None
    triggered_by: Optional[str] = None
    created_at: datetime
