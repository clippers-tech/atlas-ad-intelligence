"""Celery task: run the ATLAS rule engine across all active accounts."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "rule_engine_task"


@celery_app.task(
    name="app.tasks.rule_engine_task.run_rule_engine",
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    queue="rules",
)
def run_rule_engine(self) -> dict:  # type: ignore[override]
    """Evaluate all active rules for all active accounts and execute actions."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.rules.engine import evaluate_rules_for_account

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "actions_taken": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    actions = await evaluate_rules_for_account(db, account.id)
                    results["accounts_processed"] += 1
                    results["actions_taken"] += len(actions)
                    logger.info(
                        "rule_engine_task: account %s — %d actions",
                        account.id, len(actions),
                    )
                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("rule_engine_task: error — %s", msg)
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
        logger.exception("rule_engine_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
