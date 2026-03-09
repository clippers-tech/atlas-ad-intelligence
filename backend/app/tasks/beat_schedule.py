"""Celery Beat schedule — all periodic task definitions for ATLAS.

All times are UTC. Cron expressions follow celery.schedules.crontab syntax.
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
    # ─── Competitor scraping ───────────────────────────────────────────────
    "competitor-scrape-daily": {
        "task": "app.tasks.competitor_scrape_task.scrape_competitor_ads",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "default"},
    },
    # ─── Claude AI tasks ───────────────────────────────────────────────────
    "claude-daily-digest": {
        "task": "app.tasks.claude_daily_task.run_claude_daily_digest",
        "schedule": crontab(hour=0, minute=30),
        "options": {"queue": "ai"},
    },
    "claude-weekly-strategy": {
        "task": "app.tasks.claude_weekly_task.run_claude_weekly_strategy",
        "schedule": crontab(day_of_week=1, hour=1, minute=0),  # Monday 1 AM
        "options": {"queue": "ai"},
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
    # ─── CRM sync ──────────────────────────────────────────────────────────
    "crm-sync-daily": {
        "task": "app.tasks.crm_sync_task.sync_crm_data",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "default"},
    },
    # ─── PDF reports ───────────────────────────────────────────────────────
    "weekly-pdf-report": {
        "task": "app.tasks.report_pdf_task.generate_weekly_pdf_report",
        "schedule": crontab(day_of_week=1, hour=7, minute=0),  # Monday 7 AM
        "options": {"queue": "reports"},
    },
    # ─── System health ─────────────────────────────────────────────────────
    "health-check-every-30-min": {
        "task": "app.tasks.health_check_task.verify_system_health",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "default"},
    },
}
