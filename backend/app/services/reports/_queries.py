"""Internal DB query helpers for the report generator."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_log import ActionLog
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.campaign import Campaign
from app.models.claude_insight import ClaudeInsight
from app.models.deal import Deal
from app.models.lead import Lead

logger = logging.getLogger(__name__)


async def daily_spend_series(
    db: AsyncSession, account_id: UUID, since: datetime
) -> list[dict]:
    """Daily aggregated spend/impressions/clicks/leads for a time window."""
    result = await db.execute(
        select(
            func.date_trunc("day", AdMetric.timestamp).label("day"),
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.impressions).label("impressions"),
            func.sum(AdMetric.clicks).label("clicks"),
            func.sum(AdMetric.conversions).label("leads"),
        )
        .where(and_(AdMetric.account_id == account_id, AdMetric.timestamp >= since))
        .group_by(func.date_trunc("day", AdMetric.timestamp))
        .order_by(func.date_trunc("day", AdMetric.timestamp))
    )
    return [
        {
            "date": row.day.date().isoformat(),
            "spend": float(row.spend or 0),
            "impressions": int(row.impressions or 0),
            "clicks": int(row.clicks or 0),
            "leads": int(row.leads or 0),
            "cpl": float(row.spend or 0) / max(int(row.leads or 0), 1)
            if int(row.leads or 0) > 0
            else 0.0,
        }
        for row in result.all()
    ]


async def campaign_breakdown(
    db: AsyncSession, account_id: UUID, since: datetime
) -> list[dict]:
    """Per-campaign aggregated metrics, ordered by spend descending."""
    result = await db.execute(
        select(
            Campaign.name,
            Campaign.status,
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.impressions).label("impressions"),
            func.sum(AdMetric.clicks).label("clicks"),
            func.sum(AdMetric.conversions).label("leads"),
        )
        .join(Ad, AdMetric.ad_id == Ad.id)
        .join(Campaign, Campaign.id == Ad.ad_set_id)
        .where(and_(AdMetric.account_id == account_id, AdMetric.timestamp >= since))
        .group_by(Campaign.id, Campaign.name, Campaign.status)
        .order_by(func.sum(AdMetric.spend).desc())
    )
    return [
        {
            "campaign_name": r.name,
            "status": r.status,
            "spend": float(r.spend or 0),
            "impressions": int(r.impressions or 0),
            "clicks": int(r.clicks or 0),
            "leads": int(r.leads or 0),
            "cpl": float(r.spend or 0) / max(int(r.leads or 0), 1)
            if int(r.leads or 0) > 0
            else 0.0,
        }
        for r in result.all()
    ]


async def top_ads(
    db: AsyncSession, account_id: UUID, since: datetime, limit: int = 10
) -> list[dict]:
    """Top-performing ads by lead count in the period."""
    result = await db.execute(
        select(
            Ad.name,
            Ad.meta_ad_id,
            Ad.creative_url,
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.conversions).label("leads"),
            func.avg(AdMetric.cpl).label("avg_cpl"),
            func.avg(AdMetric.ctr).label("avg_ctr"),
        )
        .join(Ad, AdMetric.ad_id == Ad.id)
        .where(
            and_(
                AdMetric.account_id == account_id,
                AdMetric.timestamp >= since,
                AdMetric.conversions > 0,
            )
        )
        .group_by(Ad.id, Ad.name, Ad.meta_ad_id, Ad.creative_url)
        .order_by(func.sum(AdMetric.conversions).desc())
        .limit(limit)
    )
    return [
        {
            "name": r.name,
            "meta_ad_id": r.meta_ad_id,
            "creative_url": r.creative_url,
            "spend": float(r.spend or 0),
            "leads": int(r.leads or 0),
            "cpl": float(r.avg_cpl or 0),
            "ctr": float(r.avg_ctr or 0),
        }
        for r in result.all()
    ]


async def lead_pipeline(db: AsyncSession, account_id: UUID, since: datetime) -> dict:
    """Lead count and deal stage breakdown for the period."""
    lead_count = (
        await db.execute(
            select(func.count(Lead.id)).where(
                and_(Lead.account_id == account_id, Lead.created_at >= since)
            )
        )
    ).scalar_one_or_none() or 0

    stage_result = await db.execute(
        select(Deal.stage, func.count(Deal.id).label("count"))
        .join(Lead, Deal.lead_id == Lead.id)
        .where(and_(Deal.account_id == account_id, Deal.created_at >= since))
        .group_by(Deal.stage)
    )
    return {
        "total_leads": lead_count,
        "pipeline_stages": {r.stage: r.count for r in stage_result.all()},
    }


async def revenue_attribution(db: AsyncSession, account_id: UUID, since: datetime) -> dict:
    """Closed-won deal revenue and ROAS for the period."""
    rev_row = (
        await db.execute(
            select(
                func.count(Deal.id).label("closed_count"),
                func.coalesce(func.sum(Deal.revenue), 0).label("total_revenue"),
            ).where(
                and_(
                    Deal.account_id == account_id,
                    Deal.stage == "closed_won",
                    Deal.closed_at >= since,
                )
            )
        )
    ).one()

    total_spend = float(
        (
            await db.execute(
                select(func.coalesce(func.sum(AdMetric.spend), 0)).where(
                    and_(AdMetric.account_id == account_id, AdMetric.timestamp >= since)
                )
            )
        ).scalar_one() or 0
    )
    total_revenue = float(rev_row.total_revenue or 0)
    return {
        "closed_deals": int(rev_row.closed_count or 0),
        "total_revenue": total_revenue,
        "total_spend": total_spend,
        "roas": total_revenue / total_spend if total_spend > 0 else 0.0,
    }


async def system_actions_summary(
    db: AsyncSession, account_id: UUID, since: datetime
) -> list[dict]:
    """Grouped count of automated actions taken in the period."""
    result = await db.execute(
        select(ActionLog.action_type, func.count(ActionLog.id).label("count"))
        .where(and_(ActionLog.account_id == account_id, ActionLog.created_at >= since))
        .group_by(ActionLog.action_type)
        .order_by(func.count(ActionLog.id).desc())
    )
    return [{"action_type": r.action_type, "count": r.count} for r in result.all()]


async def claude_insights_for_period(
    db: AsyncSession, account_id: UUID, since: datetime, limit: int = 5
) -> list[dict]:
    """Fetch recent Claude insights generated in the period."""
    result = await db.execute(
        select(ClaudeInsight.type, ClaudeInsight.response_text, ClaudeInsight.created_at)
        .where(and_(ClaudeInsight.account_id == account_id, ClaudeInsight.created_at >= since))
        .order_by(ClaudeInsight.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "type": r.type,
            "summary": (r.response_text or "")[:400],
            "created_at": r.created_at.isoformat(),
        }
        for r in result.all()
    ]
