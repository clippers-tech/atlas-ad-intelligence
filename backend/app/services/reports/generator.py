"""Report data generator — assembles structured data for PDF export."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claude_insight import ClaudeInsight
from app.services.reports._queries import (
    campaign_breakdown,
    claude_insights_for_period,
    daily_spend_series,
    lead_pipeline,
    revenue_attribution,
    system_actions_summary,
    top_ads,
)

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def generate_weekly_report_data(db: AsyncSession, account_id: UUID) -> dict:
    """Assemble all 7-day data for PDF report rendering.

    Collects daily spend series, campaign breakdown, top ads, lead pipeline,
    revenue attribution, system actions, and Claude insights. Every query is
    filtered by account_id to prevent cross-account data leakage.

    Returns:
        Structured dict ready for PDF template rendering with keys:
        account_id, period, summary, daily_series, campaign_breakdown,
        top_ads, lead_pipeline, revenue_attribution, system_actions,
        claude_insights.
    """
    logger.info("generator: building weekly report — account_id=%s", account_id)
    since = _utcnow() - timedelta(days=7)

    daily = await daily_spend_series(db, account_id, since)
    campaigns = await campaign_breakdown(db, account_id, since)
    ads = await top_ads(db, account_id, since)
    pipeline = await lead_pipeline(db, account_id, since)
    revenue = await revenue_attribution(db, account_id, since)
    actions = await system_actions_summary(db, account_id, since)
    insights = await claude_insights_for_period(db, account_id, since)

    total_spend = sum(d["spend"] for d in daily)
    total_leads = sum(d["leads"] for d in daily)

    logger.info(
        "generator: report assembled — spend=£%.2f leads=%d campaigns=%d",
        total_spend,
        total_leads,
        len(campaigns),
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
            "avg_cpl": total_spend / total_leads if total_leads > 0 else 0.0,
        },
        "daily_series": daily,
        "campaign_breakdown": campaigns,
        "top_ads": ads,
        "lead_pipeline": pipeline,
        "revenue_attribution": revenue,
        "system_actions": actions,
        "claude_insights": insights,
    }


async def get_report_history(
    db: AsyncSession, account_id: UUID, limit: int = 20
) -> list[dict]:
    """Return report history proxied from weekly ClaudeInsight entries.

    A dedicated reports table does not yet exist. Weekly strategy insights
    serve as report anchors. All results are scoped to account_id.

    Args:
        db: Async database session.
        account_id: ATLAS account UUID.
        limit: Max entries to return (default 20).
    """
    result = await db.execute(
        select(ClaudeInsight)
        .where(
            and_(
                ClaudeInsight.account_id == account_id,
                ClaudeInsight.type == "weekly_strategy",
            )
        )
        .order_by(ClaudeInsight.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": str(ins.id),
            "type": ins.type,
            "summary": (ins.response_text or "")[:300],
            "model_used": ins.model_used,
            "tokens_used": ins.tokens_used,
            "cost_usd": ins.cost_usd,
            "created_at": ins.created_at.isoformat(),
        }
        for ins in result.scalars().all()
    ]
