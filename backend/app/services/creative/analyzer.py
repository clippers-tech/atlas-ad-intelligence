"""Creative analysis — fatigue detection, velocity scoring, placement breakdown."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_placement_metric import AdPlacementMetric
from app.models.creative_metadata import CreativeMetadata
from app.services.creative.velocity_helpers import (
    efficiency_score,
    fatigue_reason,
    trend_score,
)

logger = logging.getLogger(__name__)

_FATIGUE_WINDOW_DAYS = 7
_PLACEMENT_WINDOW_DAYS = 30
_CTR_DROP_THRESHOLD = 0.30  # 30% drop triggers fatigue
_FREQ_FATIGUE_THRESHOLD = 3.0


async def _get_active_ads(db: AsyncSession, account_id: uuid.UUID) -> list[Ad]:
    result = await db.execute(
        select(Ad).where(Ad.account_id == account_id, Ad.status == "ACTIVE")
    )
    return list(result.scalars().all())


async def _get_window_metrics(
    db: AsyncSession,
    ad_id: uuid.UUID,
    account_id: uuid.UUID,
    days: int,
) -> list[AdMetric]:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(AdMetric)
        .where(
            AdMetric.ad_id == ad_id,
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= cutoff,
        )
        .order_by(AdMetric.timestamp.asc())
    )
    return list(result.scalars().all())


async def detect_fatigue(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Detect creative fatigue for all active ads in an account.

    An ad is fatigued when CTR drops >30% from its first to latest reading
    within the last 7 days, OR when average frequency exceeds 3.0.
    Updates CreativeMetadata.is_fatigued / fatigued_at for newly flagged ads.

    Returns:
        List of dicts for ads newly flagged as fatigued this run.
    """
    ads = await _get_active_ads(db, account_id)
    newly_fatigued: list[dict[str, Any]] = []
    now = datetime.now(tz=timezone.utc)

    for ad in ads:
        metrics = await _get_window_metrics(db, ad.id, account_id, _FATIGUE_WINDOW_DAYS)
        if not metrics:
            continue

        first_ctr = metrics[0].ctr
        latest_ctr = metrics[-1].ctr
        avg_frequency = sum(m.frequency for m in metrics) / len(metrics)

        ctr_fatigued = (
            first_ctr > 0
            and (first_ctr - latest_ctr) / first_ctr >= _CTR_DROP_THRESHOLD
        )
        freq_fatigued = avg_frequency > _FREQ_FATIGUE_THRESHOLD

        if not (ctr_fatigued or freq_fatigued):
            continue

        meta_result = await db.execute(
            select(CreativeMetadata).where(
                CreativeMetadata.ad_id == ad.id,
                CreativeMetadata.account_id == account_id,
            )
        )
        creative_meta = meta_result.scalar_one_or_none()

        if creative_meta and creative_meta.is_fatigued:
            continue  # already marked

        if creative_meta:
            creative_meta.is_fatigued = True
            creative_meta.fatigued_at = now
            logger.info(
                "analyzer: ad %s flagged fatigued (ctr_drop=%s, freq=%.2f)",
                ad.id, ctr_fatigued, avg_frequency,
            )
        else:
            logger.warning(
                "analyzer: no CreativeMetadata for ad %s — skipping flag update", ad.id
            )

        ctr_drop_pct = (
            round((first_ctr - latest_ctr) / first_ctr * 100, 2) if first_ctr > 0 else 0.0
        )
        newly_fatigued.append({
            "ad_id": str(ad.id),
            "ad_name": ad.name,
            "first_ctr": round(first_ctr, 4),
            "latest_ctr": round(latest_ctr, 4),
            "ctr_drop_pct": ctr_drop_pct,
            "avg_frequency": round(avg_frequency, 2),
            "reason": fatigue_reason(ctr_fatigued, freq_fatigued),
        })

    await db.commit()
    logger.info(
        "analyzer: detect_fatigue — %d newly fatigued for account %s",
        len(newly_fatigued), account_id,
    )
    return newly_fatigued


async def score_velocity(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Score each active ad's momentum on a 0–100 scale.

    Components:
    - CTR trend       40 pts (positive trend = full marks)
    - Conversion trend 40 pts
    - Spend efficiency 20 pts (CPL vs account target_cpl)

    Returns:
        Ads with velocity scores, sorted best to worst.
    """
    from app.models.account import Account

    acct_result = await db.execute(
        select(Account.target_cpl).where(Account.id == account_id)
    )
    target_cpl: float | None = acct_result.scalar_one_or_none()

    ads = await _get_active_ads(db, account_id)
    scored: list[dict[str, Any]] = []

    for ad in ads:
        metrics = await _get_window_metrics(db, ad.id, account_id, _FATIGUE_WINDOW_DAYS)
        if len(metrics) < 2:
            continue

        ctr_vals = [m.ctr for m in metrics]
        conv_vals = [
            (m.conversions / m.impressions) if m.impressions > 0 else 0.0
            for m in metrics
        ]
        latest_cpl = metrics[-1].cpl

        ctr_pts = trend_score(ctr_vals, weight=40)
        conv_pts = trend_score(conv_vals, weight=40)
        eff_pts = efficiency_score(latest_cpl, target_cpl, weight=20)
        total = round(ctr_pts + conv_pts + eff_pts, 1)

        scored.append({
            "ad_id": str(ad.id),
            "ad_name": ad.name,
            "velocity_score": total,
            "ctr_score": round(ctr_pts, 1),
            "conv_score": round(conv_pts, 1),
            "efficiency_score": round(eff_pts, 1),
            "latest_ctr": round(ctr_vals[-1], 4),
            "latest_cpl": round(latest_cpl, 2),
        })

    scored.sort(key=lambda x: x["velocity_score"], reverse=True)
    logger.info(
        "analyzer: score_velocity — %d ads scored for account %s", len(scored), account_id
    )
    return scored


async def get_placement_breakdown(
    db: AsyncSession, ad_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Aggregate AdPlacementMetric for an ad over the last 30 days grouped by placement.

    Returns:
        List of dicts with spend, impressions, clicks, ctr, conversions per placement,
        ordered by spend descending.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=_PLACEMENT_WINDOW_DAYS)

    rows = await db.execute(
        select(
            AdPlacementMetric.placement,
            func.sum(AdPlacementMetric.spend).label("spend"),
            func.sum(AdPlacementMetric.impressions).label("impressions"),
            func.sum(AdPlacementMetric.clicks).label("clicks"),
            func.sum(AdPlacementMetric.conversions).label("conversions"),
        )
        .where(
            AdPlacementMetric.ad_id == ad_id,
            AdPlacementMetric.timestamp >= cutoff,
        )
        .group_by(AdPlacementMetric.placement)
        .order_by(func.sum(AdPlacementMetric.spend).desc())
    )

    breakdown: list[dict[str, Any]] = []
    for row in rows:
        impressions = row.impressions or 0
        clicks = row.clicks or 0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        breakdown.append({
            "placement": row.placement,
            "spend": round(float(row.spend or 0), 2),
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 4),
            "conversions": row.conversions or 0,
        })

    logger.info(
        "analyzer: placement breakdown — %d placements for ad %s", len(breakdown), ad_id
    )
    return breakdown
