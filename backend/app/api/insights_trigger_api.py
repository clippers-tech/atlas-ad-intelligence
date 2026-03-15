"""Insights trigger API — run AI insight generation via Claude."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule_log import ScheduleLog

logger = logging.getLogger(__name__)
router = APIRouter()


class TriggerRequest(BaseModel):
    account_id: str


async def _run_insight_generation(account_id: str):
    """Background task: generate insights using Claude."""
    from app.database import async_session_factory
    from app.services.insights.claude_analyzer import (
        generate_insights_for_account,
    )
    from uuid import UUID

    async with async_session_factory() as db:
        log = ScheduleLog(
            task_name="insight_generation",
            status="running",
            source="manual",
            summary=f"Manual trigger for account {account_id}",
        )
        db.add(log)
        await db.flush()
        await db.refresh(log)

        try:
            result = await generate_insights_for_account(
                db, UUID(account_id)
            )
            log.status = "completed"
            log.summary = (
                f"Generated {result.get('insights_created', 0)} "
                f"insights for account {account_id}"
            )
            log.finished_at = datetime.now(timezone.utc)
            await db.flush()
            await db.commit()
            logger.info(
                "insight trigger complete: %s", log.summary
            )
        except Exception as exc:
            log.status = "failed"
            log.error_message = str(exc)
            log.finished_at = datetime.now(timezone.utc)
            await db.flush()
            await db.commit()
            logger.error(
                "insight trigger failed for %s: %s",
                account_id, exc,
            )


@router.post("/trigger")
async def trigger_insight_generation(
    payload: TriggerRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger Claude AI insight generation for an account.

    Runs analysis in the background and stores results.
    Check /api/insights for generated insights.
    """
    background_tasks.add_task(
        _run_insight_generation, payload.account_id
    )
    logger.info(
        "Insight generation triggered for account=%s",
        payload.account_id,
    )
    return {
        "status": "processing",
        "message": (
            "Claude AI insight generation started. "
            "Results will appear on the Insights page shortly."
        ),
    }
