"""Celery task: generate weekly performance report (Monday 7 AM UTC)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "report_pdf_task"


@celery_app.task(
    name="app.tasks.report_pdf_task.generate_weekly_pdf_report",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    queue="reports",
)
def generate_weekly_pdf_report(self) -> dict:  # type: ignore[override]
    """Generate and deliver weekly report for all active accounts."""
    from sqlalchemy import select

    from app.database import async_session_factory
    from app.models.account import Account
    from app.models.health_check_log import HealthCheckLog
    from app.services.notifications.alert_formatter import format_system_alert
    from app.services.notifications.alert_router import route_alert
    from app.services.reports.generator import generate_weekly_report_data

    async def _run() -> dict:
        results: dict = {"accounts_processed": 0, "errors": []}
        async with async_session_factory() as db:
            result = await db.execute(
                select(Account).where(Account.is_active == True)  # noqa: E712
            )
            accounts = result.scalars().all()

            for account in accounts:
                try:
                    report = await generate_weekly_report_data(db, account.id)
                    results["accounts_processed"] += 1
                    logger.info(
                        "report_pdf_task: generated report for %s — "
                        "spend=%.2f, leads=%d",
                        account.name,
                        report.get("summary", {}).get("total_spend", 0),
                        report.get("summary", {}).get("total_leads", 0),
                    )

                    msg = format_system_alert(
                        f"Weekly Report Ready ({account.name})",
                        f"Period: {report.get('period', {}).get('from', '')} "
                        f"to {report.get('period', {}).get('to', '')}",
                    )
                    await route_alert(
                        "report", msg, account.telegram_chat_id
                    )
                except Exception as exc:
                    msg_str = f"account {account.id}: {exc}"
                    logger.error("report_pdf_task: error — %s", msg_str)
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
        logger.exception("report_pdf_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
