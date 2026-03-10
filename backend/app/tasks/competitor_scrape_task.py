"""Competitor scrape task — DEPRECATED.

Competitor intel is now handled by Perplexity Computer via scheduled runs.
Computer browses Meta Ad Library directly and calls POST /api/competitors/ads.
This file retained for backwards compatibility with any existing beat refs.
"""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.competitor_scrape_task.scrape_competitor_ads")
def scrape_competitor_ads() -> dict:
    """No-op — competitor scraping handled by Perplexity Computer."""
    logger.info("competitor_scrape_task: skipped — handled by Computer")
    return {"status": "skipped", "reason": "handled_by_computer"}
