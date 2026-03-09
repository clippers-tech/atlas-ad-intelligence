"""Audience health monitoring — saturation detection and performance by audience type.

manage_test_queue is defined in app.services.audience.test_queue and re-exported
here for a single import surface.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.services.audience.test_queue import manage_test_queue  # re-exported

logger = logging.getLogger(__name__)

_SATURATION_WINDOW_DAYS = 7
_FREQ_WARNING = 2.5
_FREQ_SATURATED = 4.0

__all__ = ["check_saturation", "get_audience_performance", "manage_test_queue"]


async def check_saturation(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Detect audience saturation across all active ad sets.

    Computes average frequency per ad set from the last 7 days of metrics
    (aggregated across all ads within the set).

    Thresholds:
    - avg frequency > 2.5 → "warning"
    - avg frequency > 4.0 → "saturated"

    Returns:
        Flagged ad sets with avg_frequency and status; healthy sets omitted.
    """
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=_SATURATION_WINDOW_DAYS)

    adset_result = await db.execute(
        select(AdSet).where(
            AdSet.account_id == account_id,
            AdSet.status == "ACTIVE",
        )
    )
    ad_sets = list(adset_result.scalars().all())
    flagged: list[dict[str, Any]] = []

    for ad_set in ad_sets:
        ad_ids_result = await db.execute(
            select(Ad.id).where(
                Ad.ad_set_id == ad_set.id,
                Ad.account_id == account_id,
            )
        )
        ad_ids = [row[0] for row in ad_ids_result.all()]
        if not ad_ids:
            continue

        freq_result = await db.execute(
            select(func.avg(AdMetric.frequency)).where(
                AdMetric.ad_id.in_(ad_ids),
                AdMetric.account_id == account_id,
                AdMetric.timestamp >= cutoff,
            )
        )
        avg_freq: float = freq_result.scalar_one_or_none() or 0.0

        if avg_freq <= _FREQ_WARNING:
            continue

        status = "saturated" if avg_freq > _FREQ_SATURATED else "warning"
        logger.info(
            "health: ad_set %s (%s) avg_frequency=%.2f status=%s",
            ad_set.id, ad_set.name, avg_freq, status,
        )
        flagged.append({
            "ad_set_id": str(ad_set.id),
            "ad_set_name": ad_set.name,
            "audience_type": ad_set.audience_type,
            "avg_frequency": round(avg_freq, 2),
            "status": status,
        })

    logger.info(
        "health: check_saturation — %d flagged for account %s", len(flagged), account_id
    )
    return flagged


async def get_audience_performance(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict[str, Any]]:
    """Aggregate ad performance grouped by audience_type.

    Groups all ad sets by audience_type (broad, lookalike, interest,
    custom, retargeting) and sums spend, impressions, clicks, and
    conversions to compute CTR and CPL per type.

    Returns:
        List of dicts, one per audience type, ordered by spend descending.
    """
    adset_result = await db.execute(
        select(AdSet.id, AdSet.audience_type).where(AdSet.account_id == account_id)
    )
    adsets = adset_result.all()
    if not adsets:
        return []

    type_to_adsets: dict[str, list[uuid.UUID]] = {}
    for row in adsets:
        type_to_adsets.setdefault(row.audience_type, []).append(row.id)

    performance: list[dict[str, Any]] = []

    for audience_type, adset_ids in type_to_adsets.items():
        ad_ids_result = await db.execute(
            select(Ad.id).where(
                Ad.ad_set_id.in_(adset_ids),
                Ad.account_id == account_id,
            )
        )
        ad_ids = [row[0] for row in ad_ids_result.all()]
        if not ad_ids:
            continue

        agg = await db.execute(
            select(
                func.sum(AdMetric.spend).label("spend"),
                func.sum(AdMetric.impressions).label("impressions"),
                func.sum(AdMetric.clicks).label("clicks"),
                func.sum(AdMetric.conversions).label("conversions"),
            ).where(
                AdMetric.ad_id.in_(ad_ids),
                AdMetric.account_id == account_id,
            )
        )
        row = agg.one()
        spend = float(row.spend or 0)
        impressions = int(row.impressions or 0)
        clicks = int(row.clicks or 0)
        conversions = int(row.conversions or 0)

        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        cpl = (spend / conversions) if conversions > 0 else 0.0

        performance.append({
            "audience_type": audience_type,
            "spend": round(spend, 2),
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": round(ctr, 4),
            "cpl": round(cpl, 2),
        })

    performance.sort(key=lambda x: x["spend"], reverse=True)
    logger.info(
        "health: get_audience_performance — %d types for account %s",
        len(performance), account_id,
    )
    return performance
