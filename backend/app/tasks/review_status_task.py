"""Celery task: check Meta ad review statuses and alert on disapprovals."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "review_status_task"


@celery_app.task(
    name="app.tasks.review_status_task.check_review_status_all",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    queue="meta",
)
def check_review_status_all(self) -> dict:  # type: ignore[override]
    """Check all active accounts for newly disapproved Meta ads.

    For each disapproved ad found, sends a Telegram urgent alert
    to the account's configured chat_id.
    """
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.meta.review_status import check_review_status
    from app.services.notifications.alert_formatter import format_urgent_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"accounts_checked": 0, "disapproved_ads": 0, "errors": []}

        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    disapproved = await check_review_status(
                        db, account.id, account.meta_ad_account_id
                    )
                    results["accounts_checked"] += 1

                    for ad_info in disapproved:
                        results["disapproved_ads"] += 1
                        reasons = ", ".join(ad_info.get("reject_reasons") or ["unknown"])
                        message = format_urgent_alert(
                            title=f"Ad Disapproved: {ad_info['name']}",
                            details={
                                "Meta Ad ID": ad_info["meta_ad_id"],
                                "Reject reasons": reasons,
                            },
                        )
                        await route_alert(db, account.id, "disapproved_ad", message)

                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("review_status_task: error — %s", msg)
                    results["errors"].append(msg)

            # Log task health
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
        logger.exception("review_status_task: unhandled exception — %s", exc)
        raise self.retry(exc=exc)
