"""Celery task: check market conditions (8 AM UTC daily)."""

import asyncio
import logging
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_TASK_NAME = "market_check_task"


@celery_app.task(
    name="app.tasks.market_check_task.check_market_conditions",
    bind=True,
    max_retries=1,
    default_retry_delay=300,
    queue="default",
)
def check_market_conditions(self) -> dict:  # type: ignore[override]
    """Fetch market data, update market_conditions, alert on big moves."""
    from app.database import async_session_factory
    from app.models.health_check_log import HealthCheckLog
    from app.services.market.checker import check_btc_price
    from app.services.notifications.alert_formatter import format_warning_alert
    from app.services.notifications.alert_router import route_alert

    async def _run() -> dict:
        results: dict = {"btc_checked": False, "significant": False, "errors": []}
        async with async_session_factory() as db:
            try:
                btc = await check_btc_price(db)
                results["btc_checked"] = True
                results["significant"] = btc.get("significant", False)
                results["btc_price"] = btc.get("current_price")
                results["btc_change_pct"] = btc.get("change_pct")

                if btc.get("significant"):
                    direction = "up" if btc["change_pct"] > 0 else "down"
                    msg = format_warning_alert(
                        f"BTC Price Move ({direction} {abs(btc['change_pct']):.1f}%)",
                        {
                            "Current": f"£{btc['current_price']:,.0f}",
                            "Previous": f"£{btc.get('previous_price', 0):,.0f}",
                            "Change": f"{btc['change_pct']:+.1f}%",
                        },
                    )
                    await route_alert("market", msg, None)

                logger.info(
                    "market_check_task: BTC £%s (%.1f%% change, significant=%s)",
                    btc.get("current_price"), btc.get("change_pct", 0),
                    btc.get("significant"),
                )
            except Exception as exc:
                logger.error("market_check_task: error — %s", exc)
                results["errors"].append(str(exc))

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
        logger.exception("market_check_task: unhandled — %s", exc)
        raise self.retry(exc=exc)
