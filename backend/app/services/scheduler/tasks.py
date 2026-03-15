"""Scheduler tasks — async wrappers for each scheduled automation.

Each task follows the pattern:
1. Create a ScheduleLog entry with status 'running'
2. Execute the actual work via existing service functions
3. Update the log to 'completed' or 'failed'
"""

import logging
import time
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_factory
from app.models.account import Account
from app.models.schedule_log import ScheduleLog

logger = logging.getLogger(__name__)


async def _get_active_accounts(db: AsyncSession) -> list:
    """Fetch all active accounts."""
    result = await db.execute(
        select(Account).where(Account.is_active.is_(True))
    )
    return list(result.scalars().all())


async def _create_log(
    db: AsyncSession, task_name: str, summary: str | None = None
) -> ScheduleLog:
    """Create a running ScheduleLog entry."""
    log = ScheduleLog(
        task_name=task_name,
        status="running",
        source="scheduler",
        summary=summary,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def _finish_log(
    db: AsyncSession,
    log: ScheduleLog,
    status: str,
    summary: str,
    error_message: str | None = None,
    duration_ms: int | None = None,
):
    """Mark a ScheduleLog as completed or failed."""
    log.status = status
    log.summary = summary
    log.finished_at = datetime.now(timezone.utc)
    if error_message:
        log.error_message = error_message
    if duration_ms is not None:
        log.duration_ms = duration_ms
    await db.flush()


# ── Meta Data Sync ─────────────────────────────────────────────

async def task_meta_sync():
    """Pull campaigns, ad sets, ads & metrics from Meta API."""
    logger.info("scheduler: starting meta_sync")
    start = time.monotonic()

    async with async_session_factory() as db:
        log = await _create_log(
            db, "meta_sync", "Syncing Meta data for all accounts"
        )
        try:
            from app.services.meta.campaigns_sync import sync_campaigns
            from app.services.meta.metrics_sync import sync_metrics
            from app.utils.circuit_breaker import (
                meta_circuit,
                CircuitState,
            )
            import app.utils.circuit_breaker as cb_module

            original_threshold = cb_module._FAILURE_THRESHOLD
            cb_module._FAILURE_THRESHOLD = 50
            meta_circuit._state = CircuitState.CLOSED
            meta_circuit._failure_count = 0

            accounts = await _get_active_accounts(db)
            synced, errors = [], []

            try:
                for acct in accounts:
                    meta_id = f"act_{acct.meta_ad_account_id}"
                    meta_circuit._failure_count = 0
                    meta_circuit._state = CircuitState.CLOSED
                    try:
                        await sync_campaigns(db, acct.id, meta_id)
                        await sync_metrics(db, acct.id, meta_id)
                        synced.append(acct.name)
                    except Exception as exc:
                        logger.error(
                            "meta_sync: %s failed — %s", acct.name, exc
                        )
                        errors.append(f"{acct.name}: {exc}")
            finally:
                cb_module._FAILURE_THRESHOLD = original_threshold

            duration_ms = int((time.monotonic() - start) * 1000)
            summary = f"Synced {len(synced)} accounts"
            if errors:
                summary += f", {len(errors)} errors"
            await _finish_log(
                db, log, "completed", summary,
                duration_ms=duration_ms,
                error_message="\n".join(errors) if errors else None,
            )
            await db.commit()
            logger.info("scheduler: meta_sync complete — %s", summary)

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            await _finish_log(
                db, log, "failed", "Meta sync failed",
                error_message=str(exc), duration_ms=duration_ms,
            )
            await db.commit()
            logger.error("scheduler: meta_sync failed — %s", exc)


# ── Rules Evaluation ───────────────────────────────────────────

async def task_rules_evaluation():
    """Evaluate kill, scale, bid & launch rules against latest metrics."""
    logger.info("scheduler: starting rules_evaluation")
    start = time.monotonic()

    async with async_session_factory() as db:
        log = await _create_log(
            db, "rules_evaluation",
            "Evaluating rules for all accounts",
        )
        try:
            from app.services.rules.engine import (
                evaluate_rules_for_account,
            )

            accounts = await _get_active_accounts(db)
            total_actions = 0
            errors = []

            for acct in accounts:
                try:
                    actions = await evaluate_rules_for_account(
                        db, acct.id
                    )
                    total_actions += len(actions)
                except Exception as exc:
                    logger.error(
                        "rules_evaluation: %s failed — %s",
                        acct.name, exc,
                    )
                    errors.append(f"{acct.name}: {exc}")

            duration_ms = int((time.monotonic() - start) * 1000)
            summary = (
                f"Evaluated rules for {len(accounts)} accounts, "
                f"{total_actions} actions taken"
            )
            if errors:
                summary += f", {len(errors)} errors"
            await _finish_log(
                db, log, "completed", summary,
                duration_ms=duration_ms,
                error_message="\n".join(errors) if errors else None,
            )
            await db.commit()
            logger.info(
                "scheduler: rules_evaluation complete — %s", summary
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            await _finish_log(
                db, log, "failed", "Rules evaluation failed",
                error_message=str(exc), duration_ms=duration_ms,
            )
            await db.commit()
            logger.error("scheduler: rules_evaluation failed — %s", exc)


# ── Competitor Ad Fetch ────────────────────────────────────────

async def task_competitor_fetch():
    """Fetch competitor ads via Apify for all active competitors."""
    logger.info("scheduler: starting competitor_fetch")
    start = time.monotonic()

    async with async_session_factory() as db:
        log = await _create_log(
            db, "competitor_fetch", "Fetching competitor ads"
        )
        try:
            from app.models.competitor_config import CompetitorConfig
            from app.services.competitor.apify_scraper import (
                ApifyScraperError,
                start_run,
            )

            accounts = await _get_active_accounts(db)
            total_started = 0
            errors = []

            for acct in accounts:
                configs_result = await db.execute(
                    select(CompetitorConfig).where(
                        CompetitorConfig.account_id == acct.id,
                        CompetitorConfig.is_active == True,
                        CompetitorConfig.meta_page_id.isnot(None),
                        CompetitorConfig.meta_page_id != "",
                    )
                )
                configs = configs_result.scalars().all()

                for config in configs:
                    try:
                        await start_run(
                            page_id=config.meta_page_id,
                            facebook_url=config.facebook_url,
                            country=(
                                config.scraper_country or "ALL"
                            ),
                            media_type=(
                                config.scraper_media_type or "all"
                            ),
                            platforms=(
                                config.scraper_platforms
                                or "facebook,instagram"
                            ),
                            language=(
                                config.scraper_language or "en"
                            ),
                        )
                        total_started += 1
                    except ApifyScraperError as exc:
                        errors.append(
                            f"{config.competitor_name}: {exc}"
                        )

            duration_ms = int((time.monotonic() - start) * 1000)
            summary = f"Started {total_started} competitor fetches"
            if errors:
                summary += f", {len(errors)} errors"
            await _finish_log(
                db, log, "completed", summary,
                duration_ms=duration_ms,
                error_message="\n".join(errors) if errors else None,
            )
            await db.commit()
            logger.info(
                "scheduler: competitor_fetch complete — %s", summary
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            await _finish_log(
                db, log, "failed", "Competitor fetch failed",
                error_message=str(exc), duration_ms=duration_ms,
            )
            await db.commit()
            logger.error("scheduler: competitor_fetch failed — %s", exc)


# ── Health Check ───────────────────────────────────────────────

async def task_health_check():
    """Verify backend is alive, DB connected, and data is fresh."""
    logger.info("scheduler: starting health_check")
    start = time.monotonic()

    async with async_session_factory() as db:
        log = await _create_log(
            db, "health_check", "Running health check"
        )
        try:
            from app.api.health_api import _run_health_checks

            result = await _run_health_checks(db)
            duration_ms = int((time.monotonic() - start) * 1000)
            status_str = result.get("status", "unknown")
            summary = f"System status: {status_str}"
            await _finish_log(
                db, log, "completed", summary,
                duration_ms=duration_ms,
            )
            await db.commit()
            logger.info(
                "scheduler: health_check complete — %s", summary
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            await _finish_log(
                db, log, "failed", "Health check failed",
                error_message=str(exc), duration_ms=duration_ms,
            )
            await db.commit()
            logger.error("scheduler: health_check failed — %s", exc)


# ── Insight Generation ─────────────────────────────────────────

async def task_insight_generation():
    """Generate AI insights using Claude for all accounts."""
    logger.info("scheduler: starting insight_generation")
    start = time.monotonic()

    async with async_session_factory() as db:
        log = await _create_log(
            db, "insight_generation",
            "Generating AI insights for all accounts",
        )
        try:
            from app.services.insights.claude_analyzer import (
                generate_insights_for_account,
            )

            accounts = await _get_active_accounts(db)
            total_insights = 0
            errors = []

            for acct in accounts:
                try:
                    result = await generate_insights_for_account(
                        db, acct.id
                    )
                    total_insights += result.get(
                        "insights_created", 0
                    )
                except Exception as exc:
                    logger.error(
                        "insight_generation: %s failed — %s",
                        acct.name, exc,
                    )
                    errors.append(f"{acct.name}: {exc}")

            duration_ms = int((time.monotonic() - start) * 1000)
            summary = (
                f"Generated {total_insights} insights "
                f"across {len(accounts)} accounts"
            )
            if errors:
                summary += f", {len(errors)} errors"
            await _finish_log(
                db, log, "completed", summary,
                duration_ms=duration_ms,
                error_message="\n".join(errors) if errors else None,
            )
            await db.commit()
            logger.info(
                "scheduler: insight_generation complete — %s", summary
            )

        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            await _finish_log(
                db, log, "failed", "Insight generation failed",
                error_message=str(exc), duration_ms=duration_ms,
            )
            await db.commit()
            logger.error(
                "scheduler: insight_generation failed — %s", exc
            )
