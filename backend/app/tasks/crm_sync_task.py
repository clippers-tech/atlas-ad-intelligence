"""Celery task: sync CRM data (6 AM UTC daily).

Reconciles leads and deals, recalculates attribution.
"""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "crm_sync_task"


@celery_app.task(
    name="app.tasks.crm_sync_task.sync_crm_data",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    queue="default",
)
def sync_crm_data(self) -> dict:  # type: ignore[override]
    """Sync lead and deal data, recalculate attribution."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.models.lead import Lead
    from app.services.attribution.tracker import attribute_lead

    async def _run() -> dict:
        results: dict = {"leads_attributed": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    # Find leads without attribution
                    lead_result = await db.execute(
                        select(Lead).where(
                            Lead.account_id == account.id,
                            Lead.source_ad_id.is_(None),
                        )
                    )
                    unattributed = lead_result.scalars().all()

                    for lead in unattributed:
                        attribution = await attribute_lead(db, lead.id)
                        if attribution:
                            results["leads_attributed"] += 1

                    logger.info(
                        "crm_sync_task: %s — attributed %d leads",
                        account.name, len(unattributed),
                    )
                except Exception as exc:
                    msg = f"account {account.id}: {exc}"
                    logger.error("crm_sync_task: error — %s", msg)
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
        logger.exception("crm_sync_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
