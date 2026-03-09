"""Celery task: run Claude AI daily digest analysis (12:30 AM UTC)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "claude_daily_task"


@celery_app.task(
    name="app.tasks.claude_daily_task.run_claude_daily_digest",
    bind=True,
    max_retries=1,
    default_retry_delay=600,
    queue="ai",
)
def run_claude_daily_digest(self) -> dict:  # type: ignore[override]
    """Generate Claude AI daily digest for each active account."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.claude.analyst import generate_daily_digest
    from app.services.notifications.alert_formatter import format_daily_digest
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    insight = await generate_daily_digest(db, account.id)
                    results["accounts_processed"] += 1
                    logger.info(
                        "claude_daily_task: generated digest for %s",
                        account.name,
                    )
                    # Send Telegram notification
                    digest_data = {
                        "account_name": account.name,
                        "date": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d"),
                    }
                    msg = format_daily_digest(digest_data)
                    await route_alert(
                        "daily_digest", msg, account.telegram_chat_id
                    )
                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("claude_daily_task: error — %s", msg)
                    results["errors"].append(msg)

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
        logger.exception("claude_daily_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
