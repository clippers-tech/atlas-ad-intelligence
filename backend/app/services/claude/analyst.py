"""Claude analyst — business logic for AI-powered insights."""

import json
import logging
from datetime import timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad_metric import AdMetric
from app.models.claude_memory import ClaudeMemory
from app.models.competitor_ad import CompetitorAd
from app.services.claude._helpers import (
    fetch_24h_metrics,
    fetch_memories,
    fetch_recent_actions,
    fetch_recent_insights,
    fetch_top_ads,
    save_insight,
    utcnow,
)
from app.services.claude.client import call_claude

logger = logging.getLogger(__name__)

_DAILY_SYSTEM = (
    "You are ATLAS, an expert digital advertising analyst. "
    "Analyse the provided 24-hour performance data and give concise, actionable insights. "
    "Be specific: reference actual numbers, flag anomalies, and recommend concrete next steps."
)
_WEEKLY_SYSTEM = (
    "You are ATLAS, a senior digital advertising strategist. "
    "Review the 7-day data and provide strategic recommendations. "
    "Consider trends, audience performance, competitor activity, and budget allocation."
)
_QA_SYSTEM = (
    "You are ATLAS, an expert digital advertising assistant. "
    "Answer the user's question using the provided account context. Be concise and data-driven."
)


async def generate_daily_digest(db: AsyncSession, account_id: UUID) -> dict:
    """Generate AI daily digest for an account using the last 24 hours of data.

    Gathers metrics, top ads, rule-triggered actions, and asks Claude for
    a performance assessment and next-day recommendations. Stores result
    in ClaudeInsight with type='daily_digest'.
    """
    logger.info("analyst: generating daily digest — account_id=%s", account_id)
    since_24h = utcnow() - timedelta(hours=24)

    metrics = await fetch_24h_metrics(db, account_id)
    top_ads = await fetch_top_ads(db, account_id, since_24h)
    actions = await fetch_recent_actions(db, account_id, since_24h)

    prompt = (
        f"Account 24-hour performance:\n"
        f"- Spend: £{metrics['spend']:.2f}\n"
        f"- Impressions: {metrics['impressions']:,}\n"
        f"- Clicks: {metrics['clicks']:,}\n"
        f"- Leads: {metrics['leads']}\n"
        f"- CPL: £{metrics['cpl']:.2f}\n\n"
        f"Top ads by CPL:\n{json.dumps(top_ads, indent=2)}\n\n"
        f"Automated actions taken ({len(actions)} total):\n"
        f"{json.dumps(actions[:5], indent=2)}\n\n"
        "Provide: (1) performance assessment, (2) anomalies or concerns, "
        "(3) specific recommendations for the next 24 hours."
    )

    result = await call_claude(prompt, system_prompt=_DAILY_SYSTEM)
    insight = await save_insight(db, account_id, "daily_digest", prompt, result)

    logger.info("analyst: daily digest saved — insight_id=%s", insight.id)
    return {
        "insight_id": str(insight.id),
        "type": "daily_digest",
        "response": result.get("response", ""),
        "metrics": metrics,
        "tokens_used": result.get("tokens_used", 0),
        "cost_usd": result.get("cost_usd", 0.0),
    }


async def generate_weekly_strategy(
    db: AsyncSession, account_id: UUID | None = None
) -> dict:
    """Generate weekly strategic recommendations.

    When account_id is None, aggregates across all accounts for a
    cross-account perspective. Stores result as type='weekly_strategy'
    and extracts a new ClaudeMemory learning from the response.
    """
    logger.info("analyst: generating weekly strategy — account_id=%s", account_id)
    since_7d = utcnow() - timedelta(days=7)

    metric_filters = [AdMetric.timestamp >= since_7d]
    if account_id:
        metric_filters.append(AdMetric.account_id == account_id)

    agg_result = await db.execute(
        select(
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.impressions).label("impressions"),
            func.sum(AdMetric.conversions).label("leads"),
            func.avg(AdMetric.cpl).label("avg_cpl"),
            func.avg(AdMetric.ctr).label("avg_ctr"),
        ).where(and_(*metric_filters))
    )
    agg = agg_result.one()

    top_ads = await fetch_top_ads(db, account_id, since_7d, limit=5) if account_id else []
    memories = await fetch_memories(db, account_id, limit=10)

    competitor_count = 0
    if account_id:
        comp_result = await db.execute(
            select(func.count(CompetitorAd.id)).where(
                and_(CompetitorAd.account_id == account_id, CompetitorAd.first_seen >= since_7d)
            )
        )
        competitor_count = comp_result.scalar_one_or_none() or 0

    scope = "all accounts" if not account_id else "account"
    prompt = (
        f"7-day performance summary ({scope}):\n"
        f"- Total Spend: £{float(agg.spend or 0):.2f}\n"
        f"- Impressions: {int(agg.impressions or 0):,}\n"
        f"- Leads: {int(agg.leads or 0)}\n"
        f"- Avg CPL: £{float(agg.avg_cpl or 0):.2f}\n"
        f"- Avg CTR: {float(agg.avg_ctr or 0):.2f}%\n"
        f"- New competitor ads spotted this week: {competitor_count}\n\n"
        f"Top performing ads:\n{json.dumps(top_ads, indent=2)}\n\n"
        f"Past learnings:\n" + "\n".join(f"- {m}" for m in memories) + "\n\n"
        "Provide: (1) weekly trend analysis, (2) budget reallocation recommendations, "
        "(3) audience/creative tests for next week, (4) strategic priorities."
    )

    api_result = await call_claude(prompt, system_prompt=_WEEKLY_SYSTEM)
    insight = await save_insight(db, account_id, "weekly_strategy", prompt, api_result)

    response_text = api_result.get("response", "")
    if len(response_text) > 100:
        memory = ClaudeMemory(
            account_id=account_id,
            memory_type="learning",
            content=response_text[:500],
            source_insight_id=insight.id,
            confidence_score=0.7,
        )
        db.add(memory)
        await db.commit()
        logger.info("analyst: saved ClaudeMemory from weekly strategy — insight_id=%s", insight.id)

    return {
        "insight_id": str(insight.id),
        "type": "weekly_strategy",
        "response": response_text,
        "tokens_used": api_result.get("tokens_used", 0),
        "cost_usd": api_result.get("cost_usd", 0.0),
    }


async def ask_claude(db: AsyncSession, account_id: UUID, question: str) -> dict:
    """Answer an on-demand question using recent account context and memories.

    Gathers recent metrics, actions, prior insights, and relevant memories
    to build a context-rich prompt. Stores the response as type='on_demand'.
    """
    logger.info("analyst: on-demand question — account_id=%s", account_id)
    since_7d = utcnow() - timedelta(days=7)

    metrics = await fetch_24h_metrics(db, account_id)
    actions = await fetch_recent_actions(db, account_id, since_7d, limit=5)
    memories = await fetch_memories(db, account_id)
    recent_insights = await fetch_recent_insights(db, account_id, since_7d)

    prompt = (
        f"Account context (last 24h):\n"
        f"- Spend: £{metrics['spend']:.2f}  |  Leads: {metrics['leads']}  |  CPL: £{metrics['cpl']:.2f}\n\n"
        f"Recent automated actions:\n{json.dumps(actions, indent=2)}\n\n"
        f"Recent AI insights:\n{json.dumps(recent_insights, indent=2)}\n\n"
        f"Relevant past learnings:\n" + "\n".join(f"- {m}" for m in memories) + "\n\n"
        f"User question: {question}"
    )

    result = await call_claude(prompt, system_prompt=_QA_SYSTEM)
    insight = await save_insight(db, account_id, "on_demand", prompt, result)

    logger.info("analyst: on-demand insight saved — insight_id=%s", insight.id)
    return {
        "insight_id": str(insight.id),
        "type": "on_demand",
        "question": question,
        "response": result.get("response", ""),
        "tokens_used": result.get("tokens_used", 0),
        "cost_usd": result.get("cost_usd", 0.0),
    }
