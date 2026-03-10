"""Report data generator — assembles structured data for PDF export."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reports._queries import (
    campaign_breakdown,
    daily_spend_series,
    lead_pipeline,
    revenue_attribution,
    system_actions_summary,
    top_ads,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def generate_weekly_report_data(
    db: AsyncSession, account_id: UUID
) -> dict:
    """Assemble all 7-day data for PDF report rendering.

    Collects daily spend, campaign breakdown, top ads, lead pipeline,
    revenue attribution, and system actions. Filtered by account_id.
    """
    logger.info(
        "generator: building weekly report — account_id=%s", account_id
    )
    since = _utcnow() - timedelta(days=7)

    daily = await daily_spend_series(db, account_id, since)
    campaigns = await campaign_breakdown(db, account_id, since)
    ads = await top_ads(db, account_id, since)
    pipeline = await lead_pipeline(db, account_id, since)
    revenue = await revenue_attribution(db, account_id, since)
    actions = await system_actions_summary(db, account_id, since)

    total_spend = sum(d["spend"] for d in daily)
    total_leads = sum(d["leads"] for d in daily)

    logger.info(
        "generator: report assembled — spend=£%.2f leads=%d",
        total_spend,
        total_leads,
    )

    return {
        "account_id": str(account_id),
        "period": {
            "start": since.date().isoformat(),
            "end": _utcnow().date().isoformat(),
        },
        "summary": {
            "total_spend": total_spend,
            "total_leads": total_leads,
            "avg_cpl": (
                total_spend / total_leads if total_leads > 0 else 0.0
            ),
        },
        "daily_series": daily,
        "campaign_breakdown": campaigns,
        "top_ads": ads,
        "lead_pipeline": pipeline,
        "revenue_attribution": revenue,
        "system_actions": actions,
    }
