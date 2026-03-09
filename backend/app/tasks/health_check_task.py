"""Celery task: verify that critical tasks have run within their expected windows."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Alert if these tasks have not run within the specified minutes
_TASK_WINDOWS: dict[str, int] = {
    "meta_pull_task": 20,
    "rule_engine_task": 20,
}


@celery_app.task(
    name="app.tasks.health_check_task.verify_system_health",
    queue="default",
)
def verify_system_health() -> dict:
    """Check health_check_logs to confirm critical tasks ran recently.

    Sends a Telegram system alert if any task has missed its window.
    """
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.health_check_log import HealthCheckLog
    from app.services.notifications.alert_formatter import format_system_alert
    from app.services.notifications.alert_router import route_system_alert

    async def _run() -> dict:
        results: dict = {"checked": [], "alerts_sent": 0}
        now = datetime.now(tz=timezone.utc)

        async with async_session_factory() as db:
            for task_name, max_age_minutes in _TASK_WINDOWS.items():
                cutoff = now - timedelta(minutes=max_age_minutes)

                result = await db.execute(
                    select(HealthCheckLog)
                    .where(HealthCheckLog.task_name == task_name)
                    .order_by(HealthCheckLog.last_run_at.desc())
                    .limit(1)
                )
                log = result.scalar_one_or_none()

                status = "ok"
                if log is None:
                    status = "never_run"
                    logger.warning("health_check: task '%s' has NEVER run", task_name)
                elif log.last_run_at < cutoff:
                    age_min = int((now - log.last_run_at).total_seconds() / 60)
                    status = f"missed_{age_min}min"
                    logger.warning(
                        "health_check: task '%s' last ran %d minutes ago (threshold: %d min)",
                        task_name, age_min, max_age_minutes,
                    )

                results["checked"].append({"task": task_name, "status": status})

                if status != "ok":
                    message = format_system_alert(
                        title=f"Task missed: {task_name}",
                        details={
                            "Status": status,
                            "Threshold": f"{max_age_minutes} minutes",
                            "Checked at": now.strftime("%Y-%m-%d %H:%M UTC"),
                        },
                    )
                    sent = await route_system_alert(message)
                    if sent:
                        results["alerts_sent"] += 1

        return results

    return asyncio.run(_run())
