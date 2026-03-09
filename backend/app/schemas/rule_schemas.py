from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RuleCreate(BaseModel):
    account_id: UUID
    name: str
    description: Optional[str] = None
    type: str
    condition_json: dict[str, Any]
    action_json: dict[str, Any]
    is_enabled: bool = True
    priority: int = 0
    cooldown_minutes: int = 60


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    condition_json: Optional[dict[str, Any]] = None
    action_json: Optional[dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    cooldown_minutes: Optional[int] = None


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    name: str
    description: Optional[str] = None
    type: str
    condition_json: dict[str, Any]
    action_json: dict[str, Any]
    is_enabled: bool
    priority: int
    cooldown_minutes: int
    created_at: datetime
    updated_at: datetime
