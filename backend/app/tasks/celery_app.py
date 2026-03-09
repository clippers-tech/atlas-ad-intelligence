"""Celery application factory for ATLAS.

Broker and result backend are read from the REDIS_URL environment variable,
falling back to the Redis service defined in docker-compose.
"""

import os

from celery import Celery

from app.tasks.beat_schedule import CELERY_BEAT_SCHEDULE

os.environ.setdefault("CELERY_CONFIG_MODULE", "app.config")

_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery("atlas")

celery_app.config_from_object(
    {
        # Broker + backend
        "broker_url": _REDIS_URL,
        "result_backend": _REDIS_URL,
        # Serialisation
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        # Timezone
        "timezone": "UTC",
        "enable_utc": True,
        # Beat schedule
        "beat_schedule": CELERY_BEAT_SCHEDULE,
        # Queues — match the 'queue' options in beat_schedule
        "task_default_queue": "default",
        "task_routes": {
            "app.tasks.meta_pull_task.*": {"queue": "meta"},
            "app.tasks.review_status_task.*": {"queue": "meta"},
            "app.tasks.rule_engine_task.*": {"queue": "rules"},
            "app.tasks.claude_daily_task.*": {"queue": "ai"},
            "app.tasks.claude_weekly_task.*": {"queue": "ai"},
            "app.tasks.report_pdf_task.*": {"queue": "reports"},
        },
        # Worker config
        "worker_prefetch_multiplier": 1,
        "task_acks_late": True,
        "task_reject_on_worker_lost": True,
        # Result expiry (24 hours)
        "result_expires": 86400,
    }
)

# Auto-discover all task modules in app.tasks package
celery_app.autodiscover_tasks(
    [
        "app.tasks.meta_pull_task",
        "app.tasks.review_status_task",
        "app.tasks.health_check_task",
        "app.tasks.rule_engine_task",
        "app.tasks.competitor_scrape_task",
        "app.tasks.claude_daily_task",
        "app.tasks.claude_weekly_task",
        "app.tasks.market_check_task",
        "app.tasks.creative_velocity_task",
        "app.tasks.audience_health_task",
        "app.tasks.report_pdf_task",
        "app.tasks.crm_sync_task",
    ]
)
