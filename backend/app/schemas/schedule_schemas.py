"""Pydantic schemas for schedule log endpoints."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScheduleLogCreate(BaseModel):
    task_name: str
    status: str = "running"
    source: str = "computer"
    summary: Optional[str] = None


class ScheduleLogUpdate(BaseModel):
    status: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    finished_at: Optional[datetime] = None


class ScheduleLogResponse(BaseModel):
    id: str
    task_name: str
    status: str
    source: str
    summary: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None

    class Config:
        from_attributes = True
