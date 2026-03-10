"""Health check API — system status and task run times."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import select, text

from app.database import async_session_factory
from app.models.health_check_log import HealthCheckLog

logger = logging.getLogger(__name__)
router = APIRouter()

TRACKED_TASKS = [
    "meta_pull",
    "rule_engine",
    "market_check",
    "creative_velocity",
]


@router.get("/health")
async def health_check():
    """Return system health. Works even without a DB connection."""
    db_status = "not_configured"
    task_statuses = {t: {"status": "unknown"} for t in TRACKED_TASKS}

    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
            db_status = "ok"

            for task_name in TRACKED_TASKS:
                result = await db.execute(
                    select(HealthCheckLog)
                    .where(HealthCheckLog.task_name == task_name)
                    .order_by(HealthCheckLog.last_run_at.desc())
                    .limit(1)
                )
                log = result.scalar_one_or_none()
                task_statuses[task_name] = {
                    "last_run_at": (
                        log.last_run_at.isoformat() if log else None
                    ),
                    "status": log.status if log else "never_run",
                    "error_message": (
                        log.error_message if log else None
                    ),
                }
    except Exception as exc:
        logger.warning("DB unavailable in health check: %s", exc)

    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "tasks": task_statuses,
    }
