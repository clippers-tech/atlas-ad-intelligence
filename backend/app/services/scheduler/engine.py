"""ATLAS Scheduler Engine — APScheduler-based cron job manager.

Runs inside the FastAPI process using AsyncIOScheduler.
Suitable for single-process deployments on Render.

Registered jobs:
    meta_sync           — Every 4 hours (minute 0)
    rules_evaluation    — Every 4 hours (minute 15, offset after sync)
    competitor_fetch    — Every 4 hours (minute 30)
    health_check        — Every 4 hours (minute 45)
    insight_generation  — Every 4 hours (minute 50)
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _register_jobs(scheduler: AsyncIOScheduler) -> None:
    """Register all ATLAS cron jobs."""

    from app.services.scheduler.tasks import (
        task_meta_sync,
        task_rules_evaluation,
        task_competitor_fetch,
        task_health_check,
        task_insight_generation,
    )

    # ── Meta Data Sync — every 4 hours at :00 ──────────────────
    scheduler.add_job(
        task_meta_sync,
        CronTrigger(hour="*/4", minute=0),
        id="meta_sync",
        name="ATLAS Meta Data Sync",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # ── Rules Evaluation — every 4 hours at :15 ───────────────
    scheduler.add_job(
        task_rules_evaluation,
        CronTrigger(hour="*/4", minute=15),
        id="rules_evaluation",
        name="ATLAS Rules Evaluation",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # ── Competitor Ad Fetch — every 4 hours at :30 ─────────────
    scheduler.add_job(
        task_competitor_fetch,
        CronTrigger(hour="*/4", minute=30),
        id="competitor_fetch",
        name="ATLAS Competitor Ad Fetch",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # ── Health Check — every 4 hours at :45 ────────────────────
    scheduler.add_job(
        task_health_check,
        CronTrigger(hour="*/4", minute=45),
        id="health_check",
        name="ATLAS Health Check",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # ── AI Insight Generation — every 4 hours at :50 ───────────
    scheduler.add_job(
        task_insight_generation,
        CronTrigger(hour="*/4", minute=50),
        id="insight_generation",
        name="ATLAS Daily AI Insights",
        replace_existing=True,
        misfire_grace_time=600,
    )


def start_scheduler() -> None:
    """Start the ATLAS scheduler. Call from FastAPI startup."""
    global _scheduler

    if _scheduler is not None:
        logger.warning("scheduler: already running, skipping start")
        return

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _register_jobs(_scheduler)
    _scheduler.start()

    # Log next run times for each job
    for job in _scheduler.get_jobs():
        logger.info(
            "scheduler: registered '%s' — next run: %s",
            job.name,
            job.next_run_time,
        )

    logger.info(
        "scheduler: started with %d jobs",
        len(_scheduler.get_jobs()),
    )


def stop_scheduler() -> None:
    """Shutdown the ATLAS scheduler. Call from FastAPI shutdown."""
    global _scheduler

    if _scheduler is None:
        return

    _scheduler.shutdown(wait=False)
    logger.info("scheduler: stopped")
    _scheduler = None


def get_scheduler_status() -> dict:
    """Return current scheduler status and next run times."""
    if _scheduler is None:
        return {"status": "stopped", "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": (
                job.next_run_time.isoformat()
                if job.next_run_time
                else None
            ),
        })

    return {
        "status": "running",
        "jobs": jobs,
        "total_jobs": len(jobs),
    }
