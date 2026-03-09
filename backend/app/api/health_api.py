"""Health check API — system status and task run times."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.health_check_log import HealthCheckLog

logger = logging.getLogger(__name__)
router = APIRouter()

TRACKED_TASKS = [
    "meta_pull",
    "rule_engine",
    "claude_digest",
    "competitor_scraper",
]


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Return system health status and last run times for all background tasks."""
    task_statuses = {}

    for task_name in TRACKED_TASKS:
        result = await db.execute(
            select(HealthCheckLog)
            .where(HealthCheckLog.task_name == task_name)
            .order_by(HealthCheckLog.last_run_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        task_statuses[task_name] = {
            "last_run_at": log.last_run_at.isoformat() if log else None,
            "status": log.status if log else "never_run",
            "error_message": log.error_message if log else None,
        }

    # Check DB connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        db_status = "error"

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "tasks": task_statuses,
        "last_meta_pull": task_statuses.get("meta_pull", {}).get("last_run_at"),
        "last_rule_engine_run": task_statuses.get("rule_engine", {}).get("last_run_at"),
    }
