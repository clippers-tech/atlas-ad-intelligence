"""Celery task: analyse creative velocity (9 AM UTC daily)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "creative_velocity_task"


@celery_app.task(
    name="app.tasks.creative_velocity_task.analyse_creative_velocity",
    bind=True,
    max_retries=1,
    default_retry_delay=120,
    queue="default",
)
def analyse_creative_velocity(self) -> dict:  # type: ignore[override]
    """Analyse creative fatigue rates and alert on fast-fatiguing ads."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.creative.analyzer import detect_fatigue, score_velocity
    from app.services.notifications.alert_formatter import format_warning_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "fatigued": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    fatigued = await detect_fatigue(db, account.id)
                    await score_velocity(db, account.id)
                    results["accounts_processed"] += 1
                    results["fatigued"] += len(fatigued)

                    if fatigued:
                        names = ", ".join(f["ad_name"] for f in fatigued[:3])
                        msg = format_warning_alert(
                            f"Creative Fatigue ({account.name})",
                            f"{len(fatigued)} ads fatigued: {names}",
                        )
                        await route_alert(
                            "creative", msg, account.telegram_chat_id
                        )

                    logger.info(
                        "creative_velocity_task: %s — %d fatigued",
                        account.name, len(fatigued),
                    )
                except Exception as exc:
                    msg_str = f"account {account.id}: {exc}"
                    logger.error("creative_velocity_task: error — %s", msg_str)
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
        logger.exception("creative_velocity_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
