from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClaudeAskRequest(BaseModel):
    account_id: Optional[UUID] = None
    question: str
    context: Optional[str] = None


class ClaudeInsightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: Optional[UUID] = None
    type: str
    response_text: str
    recommendations_json: Optional[list[Any]] = None
    model_used: str
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    created_at: datetime


class ClaudeMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: Optional[UUID] = None
    memory_type: str
    content: str
    confidence_score: Optional[float] = None
    tags_json: Optional[list[str]] = None
    created_at: datetime
