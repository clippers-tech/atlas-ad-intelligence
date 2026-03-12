"""Insights trigger API — queue an AI insight generation run."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule_log import ScheduleLog

logger = logging.getLogger(__name__)
router = APIRouter()


class TriggerRequest(BaseModel):
    account_id: str


@router.post("/trigger")
async def trigger_insight_generation(
    payload: TriggerRequest,
    db: AsyncSession = Depends(get_db),
):
    """Queue an insight generation run.

    Creates a schedule log entry with status 'pending' that
    Computer picks up on its next check, or the cron handles.
    """
    log = ScheduleLog(
        task_name="insight_generation",
        status="pending",
        source="manual",
        summary=f"Manual trigger for account {payload.account_id}",
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    logger.info(
        "Insight generation queued for account=%s",
        payload.account_id,
    )
    return {
        "status": "queued",
        "message": "Insight generation has been queued. Results will appear shortly.",
        "log_id": str(log.id),
    }
