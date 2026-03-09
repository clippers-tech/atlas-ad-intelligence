"""Celery task: pull Meta campaigns and metrics for all active accounts."""

import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "meta_pull_task"


@celery_app.task(
    name="app.tasks.meta_pull_task.pull_meta_metrics",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="meta",
)
def pull_meta_metrics(self) -> dict:  # type: ignore[override]
    """Pull Meta campaign data and metrics for every active account.

    This task is a thin synchronous wrapper that runs async services via
    asyncio. All heavy logic lives in services/meta/.
    """
    import asyncio

    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.meta.campaigns_sync import sync_campaigns
    from app.services.meta.metrics_sync import sync_metrics

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    await sync_campaigns(db, account.id, account.meta_ad_account_id)
                    await sync_metrics(db, account.id, account.meta_ad_account_id)
                    results["accounts_processed"] += 1
                    logger.info("meta_pull_task: processed account %s", account.id)
                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("meta_pull_task: error — %s", msg)
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
        logger.exception("meta_pull_task: unhandled exception — %s", exc)
        raise self.retry(exc=exc)
