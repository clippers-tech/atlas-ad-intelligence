"""Internal helpers for Claude analyst — DB queries and prompt utilities."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_log import ActionLog
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.claude_insight import ClaudeInsight
from app.models.claude_memory import ClaudeMemory

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def fetch_24h_metrics(db: AsyncSession, account_id: UUID) -> dict:
    """Aggregate spend, impressions, clicks, conversions for the last 24 hours."""
    from datetime import timedelta
    since = utcnow() - timedelta(hours=24)
    result = await db.execute(
        select(
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.impressions).label("impressions"),
            func.sum(AdMetric.clicks).label("clicks"),
            func.sum(AdMetric.conversions).label("leads"),
        ).where(and_(AdMetric.account_id == account_id, AdMetric.timestamp >= since))
    )
    row = result.one()
    spend = float(row.spend or 0)
    leads = int(row.leads or 0)
    return {
        "spend": spend,
        "impressions": int(row.impressions or 0),
        "clicks": int(row.clicks or 0),
        "leads": leads,
        "cpl": spend / leads if leads > 0 else 0.0,
    }


async def fetch_top_ads(
    db: AsyncSession, account_id: UUID, since: datetime, limit: int = 3
) -> list[dict]:
    """Fetch top-performing ads by CPL (ascending) for a given time window."""
    result = await db.execute(
        select(
            Ad.name,
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.conversions).label("leads"),
            func.avg(AdMetric.cpl).label("avg_cpl"),
        )
        .join(Ad, AdMetric.ad_id == Ad.id)
        .where(
            and_(
                AdMetric.account_id == account_id,
                AdMetric.timestamp >= since,
                AdMetric.conversions > 0,
            )
        )
        .group_by(Ad.id, Ad.name)
        .order_by(func.avg(AdMetric.cpl).asc())
        .limit(limit)
    )
    return [
        {
            "name": row.name,
            "spend": float(row.spend or 0),
            "leads": int(row.leads or 0),
            "cpl": float(row.avg_cpl or 0),
        }
        for row in result.all()
    ]


async def fetch_recent_actions(
    db: AsyncSession, account_id: UUID, since: datetime, limit: int = 20
) -> list[dict]:
    """Fetch recent automated actions from ActionLog."""
    result = await db.execute(
        select(ActionLog.action_type, ActionLog.details_json, ActionLog.created_at)
        .where(and_(ActionLog.account_id == account_id, ActionLog.created_at >= since))
        .order_by(ActionLog.created_at.desc())
        .limit(limit)
    )
    return [
        {"action": row.action_type, "details": row.details_json, "at": row.created_at.isoformat()}
        for row in result.all()
    ]


async def fetch_memories(
    db: AsyncSession, account_id: UUID | None, limit: int = 10
) -> list[str]:
    """Fetch active ClaudeMemory entries for account (plus global ones)."""
    filters = [ClaudeMemory.is_active == True]  # noqa: E712
    if account_id:
        filters.append(ClaudeMemory.account_id.in_([account_id, None]))
    result = await db.execute(
        select(ClaudeMemory.content)
        .where(and_(*filters))
        .order_by(ClaudeMemory.confidence_score.desc())
        .limit(limit)
    )
    return [row.content for row in result.all()]


async def fetch_recent_insights(
    db: AsyncSession, account_id: UUID, since: datetime, limit: int = 3
) -> list[dict]:
    """Fetch recent ClaudeInsights for context."""
    result = await db.execute(
        select(ClaudeInsight.type, ClaudeInsight.response_text, ClaudeInsight.created_at)
        .where(and_(ClaudeInsight.account_id == account_id, ClaudeInsight.created_at >= since))
        .order_by(ClaudeInsight.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "type": r.type,
            "summary": (r.response_text or "")[:200],
            "at": r.created_at.isoformat(),
        }
        for r in result.all()
    ]


async def save_insight(
    db: AsyncSession,
    account_id: UUID | None,
    insight_type: str,
    prompt_text: str,
    api_result: dict,
) -> ClaudeInsight:
    """Persist a ClaudeInsight row and return it."""
    insight = ClaudeInsight(
        account_id=account_id,
        type=insight_type,
        prompt_text=prompt_text[:4000],
        response_text=api_result.get("response", ""),
        model_used=api_result.get("model"),
        tokens_used=api_result.get("tokens_used"),
        cost_usd=api_result.get("cost_usd"),
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    logger.debug("analyst: saved %s insight — id=%s", insight_type, insight.id)
    return insight
