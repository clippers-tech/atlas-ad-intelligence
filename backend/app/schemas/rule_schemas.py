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
    budget_limit: Optional[float] = None


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    condition_json: Optional[dict[str, Any]] = None
    action_json: Optional[dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    priority: Optional[int] = None
    cooldown_minutes: Optional[int] = None
    budget_limit: Optional[float] = None
    budget_spent: Optional[float] = None


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    name: str
    description: Optional[str] = None
    type: str
    condition_json: Any  # Stored as JSON string in DB, parsed in API
    action_json: Any  # Stored as JSON string in DB, parsed in API
    is_enabled: bool
    priority: int
    cooldown_minutes: int
    budget_limit: Optional[float] = None
    budget_spent: float = 0.0
    created_at: datetime
    updated_at: datetime
