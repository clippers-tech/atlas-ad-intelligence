"""Celery task: scrape competitor ad libraries via Apify (2 AM UTC daily)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "competitor_scrape_task"


@celery_app.task(
    name="app.tasks.competitor_scrape_task.scrape_competitor_ads",
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    queue="default",
)
def scrape_competitor_ads(self) -> dict:  # type: ignore[override]
    """Collect competitor ads from Facebook Ad Library via Apify actor."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.competitor.scraper import detect_new_ads, scrape_competitors
    from app.services.notifications.alert_formatter import format_warning_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "new_ads": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    scrape_result = await scrape_competitors(db, account.id)
                    new_ads = await detect_new_ads(db, account.id, since_hours=24)
                    results["accounts_processed"] += 1
                    results["new_ads"] += len(new_ads)

                    if new_ads:
                        msg = format_warning_alert(
                            f"New Competitor Ads ({account.name})",
                            f"{len(new_ads)} new ads detected",
                        )
                        await route_alert(
                            "competitor", msg, account.telegram_chat_id
                        )

                    logger.info(
                        "competitor_scrape_task: %s — %d new ads",
                        account.name, len(new_ads),
                    )
                except Exception as exc:
                    msg_str = f"account {account.id}: {exc}"
                    logger.error("competitor_scrape_task: error — %s", msg_str)
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
        logger.exception("competitor_scrape_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
