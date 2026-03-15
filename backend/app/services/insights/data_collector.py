"""Data collector — gathers metrics and context for Claude analysis.

Assembles a structured data snapshot for a single account,
including campaign metrics, lead pipeline, competitor intel,
recent rule actions, and anomalies.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.campaign import Campaign
from app.models.lead import Lead
from app.models.action_log import ActionLog
from app.models.competitor_ad import CompetitorAd
from app.models.competitor_config import CompetitorConfig

logger = logging.getLogger(__name__)


async def collect_account_data(
    db: AsyncSession, account_id: UUID
) -> dict:
    """Gather all relevant data for Claude analysis.

    Returns a structured dict with:
    - account info
    - campaign performance (last 7 days)
    - top/bottom ads
    - lead pipeline summary
    - recent rule actions
    - competitor activity
    """
    since = datetime.now(timezone.utc) - timedelta(days=7)

    # ── Account info ───────────────────────────────────────────
    acct = await db.get(Account, account_id)
    if not acct:
        return {"error": "Account not found"}

    account_info = {
        "name": acct.name,
        "business_type": acct.business_type,
        "target_cpl": acct.target_cpl,
        "target_cpa": acct.target_cpa,
        "target_roas": acct.target_roas,
        "currency": acct.currency,
    }

    # ── Campaign performance ───────────────────────────────────
    campaigns_result = await db.execute(
        select(Campaign).where(
            Campaign.account_id == account_id
        )
    )
    campaigns = campaigns_result.scalars().all()

    campaign_data = []
    for camp in campaigns:
        metrics_result = await db.execute(
            select(
                func.sum(AdMetric.spend).label("spend"),
                func.sum(AdMetric.impressions).label(
                    "impressions"
                ),
                func.sum(AdMetric.clicks).label("clicks"),
                func.sum(AdMetric.conversions).label(
                    "conversions"
                ),
            )
            .join(Ad, Ad.id == AdMetric.ad_id)
            .where(
                Ad.account_id == account_id,
                AdMetric.account_id == account_id,
                AdMetric.timestamp >= since,
            )
        )
        row = metrics_result.one()
        spend = float(row.spend or 0)
        impressions = int(row.impressions or 0)
        clicks = int(row.clicks or 0)
        conversions = int(row.conversions or 0)

        campaign_data.append({
            "name": camp.name,
            "status": camp.status,
            "spend": round(spend, 2),
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": (
                round(clicks / impressions * 100, 2)
                if impressions > 0
                else 0
            ),
            "cpl": (
                round(spend / conversions, 2)
                if conversions > 0
                else 0
            ),
        })

    # ── Total metrics summary ──────────────────────────────────
    total_spend = sum(c["spend"] for c in campaign_data)
    total_conversions = sum(
        c["conversions"] for c in campaign_data
    )
    total_clicks = sum(c["clicks"] for c in campaign_data)
    total_impressions = sum(
        c["impressions"] for c in campaign_data
    )

    metrics_summary = {
        "period": "last_7_days",
        "total_spend": round(total_spend, 2),
        "total_conversions": total_conversions,
        "total_clicks": total_clicks,
        "total_impressions": total_impressions,
        "avg_cpl": (
            round(total_spend / total_conversions, 2)
            if total_conversions > 0
            else 0
        ),
        "avg_ctr": (
            round(total_clicks / total_impressions * 100, 2)
            if total_impressions > 0
            else 0
        ),
    }

    # ── Lead pipeline ──────────────────────────────────────────
    leads_result = await db.execute(
        select(Lead.stage, func.count(Lead.id)).where(
            Lead.account_id == account_id,
            Lead.created_at >= since,
        ).group_by(Lead.stage)
    )
    lead_pipeline = {
        row[0]: row[1] for row in leads_result.all()
    }

    # ── Recent rule actions ────────────────────────────────────
    actions_result = await db.execute(
        select(
            ActionLog.action_type,
            func.count(ActionLog.id),
        )
        .where(
            ActionLog.account_id == account_id,
            ActionLog.created_at >= since,
        )
        .group_by(ActionLog.action_type)
    )
    rule_actions = {
        row[0]: row[1] for row in actions_result.all()
    }

    # ── Competitor activity ────────────────────────────────────
    competitor_data = []
    configs_result = await db.execute(
        select(CompetitorConfig).where(
            CompetitorConfig.account_id == account_id,
            CompetitorConfig.is_active == True,
        )
    )
    for config in configs_result.scalars().all():
        ads_count = (
            await db.execute(
                select(func.count(CompetitorAd.id)).where(
                    CompetitorAd.competitor_config_id
                    == config.id,
                    CompetitorAd.is_active == True,
                )
            )
        ).scalar() or 0
        competitor_data.append({
            "name": config.competitor_name,
            "active_ads": ads_count,
        })

    return {
        "account": account_info,
        "metrics_summary": metrics_summary,
        "campaigns": campaign_data,
        "lead_pipeline": lead_pipeline,
        "rule_actions": rule_actions,
        "competitors": competitor_data,
        "data_period": {
            "from": since.isoformat(),
            "to": datetime.now(timezone.utc).isoformat(),
        },
    }
