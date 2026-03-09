"""Celery task: check audience health (9:30 AM UTC daily)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "audience_health_task"


@celery_app.task(
    name="app.tasks.audience_health_task.check_audience_health",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    queue="default",
)
def check_audience_health(self) -> dict:  # type: ignore[override]
    """Evaluate audience health metrics and flag exhausted audiences."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.audience.health import check_saturation
    from app.services.audience.test_queue import manage_test_queue
    from app.services.notifications.alert_formatter import format_warning_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {
            "accounts_processed": 0, "saturated": 0,
            "graduated": 0, "killed": 0, "errors": [],
        }
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    saturation = await check_saturation(db, account.id)
                    queue_result = await manage_test_queue(db, account.id)
                    results["accounts_processed"] += 1

                    saturated = [s for s in saturation if s["status"] == "saturated"]
                    results["saturated"] += len(saturated)
                    results["graduated"] += len(queue_result.get("graduated", []))
                    results["killed"] += len(queue_result.get("killed", []))

                    if saturated:
                        names = ", ".join(s["adset_name"] for s in saturated[:3])
                        msg = format_warning_alert(
                            f"Audience Saturation ({account.name})",
                            f"{len(saturated)} saturated: {names}",
                        )
                        await route_alert(
                            "audience", msg, account.telegram_chat_id
                        )

                    logger.info(
                        "audience_health_task: %s — %d saturated, %d graduated, %d killed",
                        account.name, len(saturated),
                        len(queue_result.get("graduated", [])),
                        len(queue_result.get("killed", [])),
                    )
                except Exception as exc:
                    msg_str = f"account {account.id}: {exc}"
                    logger.error("audience_health_task: error — %s", msg_str)
                    results["errors"].append(msg_str)

            log = HealthCheckLog(
                task_name=_TASK_NAME,
                last_run_at=datetime.now(tz=timezone.utc),
                status="failed" if results["errors"] else "success",
                error_message="; ".join(results["errors"]) or None,
            )
            db.add(log)
            await db.commit()

        return results

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.exception("audience_health_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
