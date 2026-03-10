"""Celery Beat schedule — all periodic task definitions for ATLAS.

All times are UTC. Cron expressions follow celery.schedules.crontab syntax.

NOTE: AI analysis (daily digests, weekly strategy) and competitor intel
are handled by Perplexity Computer via scheduled runs — not Celery.
"""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE: dict = {
    # ─── Meta data pulls ───────────────────────────────────────────────────
    "meta-pull-every-15-min": {
        "task": "app.tasks.meta_pull_task.pull_meta_metrics",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "meta"},
    },
    # ─── Rule engine ───────────────────────────────────────────────────────
    "rule-engine-every-15-min": {
        "task": "app.tasks.rule_engine_task.run_rule_engine",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "rules"},
    },
    # ─── Ad review status ──────────────────────────────────────────────────
    "review-status-every-15-min": {
        "task": "app.tasks.review_status_task.check_review_status_all",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "meta"},
    },
    # ─── Market conditions ─────────────────────────────────────────────────
    "market-check-daily": {
        "task": "app.tasks.market_check_task.check_market_conditions",
        "schedule": crontab(hour=8, minute=0),
        "options": {"queue": "default"},
    },
    # ─── Creative & audience analysis ──────────────────────────────────────
    "creative-velocity-daily": {
        "task": "app.tasks.creative_velocity_task.analyse_creative_velocity",
        "schedule": crontab(hour=9, minute=0),
        "options": {"queue": "default"},
    },
    "audience-health-daily": {
        "task": "app.tasks.audience_health_task.check_audience_health",
        "schedule": crontab(hour=9, minute=30),
        "options": {"queue": "default"},
    },
    # ─── System health ─────────────────────────────────────────────────────
    "health-check-every-30-min": {
        "task": "app.tasks.health_check_task.verify_system_health",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "default"},
    },
}
