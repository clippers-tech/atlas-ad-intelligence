"""Celery task: run Claude AI weekly strategy analysis (Monday 1 AM UTC)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "claude_weekly_task"


@celery_app.task(
    name="app.tasks.claude_weekly_task.run_claude_weekly_strategy",
    bind=True,
    max_retries=1,
    default_retry_delay=600,
    queue="ai",
)
def run_claude_weekly_strategy(self) -> dict:  # type: ignore[override]
    """Generate Claude AI weekly strategy review for each active account."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.claude.analyst import generate_weekly_strategy
    from app.services.notifications.alert_formatter import format_system_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            # Per-account strategy
            for account in accounts:
                try:
                    await generate_weekly_strategy(db, account.id)
                    results["accounts_processed"] += 1
                    logger.info(
                        "claude_weekly_task: generated strategy for %s",
                        account.name,
                    )
                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("claude_weekly_task: error — %s", msg)
                    results["errors"].append(msg)

            # Cross-account strategy (account_id=None)
            try:
                await generate_weekly_strategy(db, account_id=None)
                logger.info("claude_weekly_task: generated cross-account strategy")
            except Exception as exc:
                logger.error("claude_weekly_task: cross-account error — %s", exc)
                results["errors"].append(f"cross-account: {exc}")

            # Notify
            msg = format_system_alert(
                "Weekly Strategy Complete",
                f"Processed {results['accounts_processed']} accounts",
            )
            await route_alert("system", msg, None)

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
        logger.exception("claude_weekly_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
