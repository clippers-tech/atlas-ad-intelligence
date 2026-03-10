"""Sync Meta ad-level insights into ad_metrics table.

Pulls daily spend/impressions/clicks/conversions for each ad,
upserting one row per ad per day.
"""

import logging
import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

_INSIGHT_FIELDS = (
    "ad_id,date_start,spend,impressions,clicks,ctr,cpc,cpm,"
    "reach,frequency,actions,cost_per_action_type"
)


def _parse_actions(actions: list[dict] | None, key: str) -> int:
    """Extract a specific action count from Meta actions array."""
    if not actions:
        return 0
    for a in actions:
        if a.get("action_type") == key:
            return int(a.get("value", 0))
    return 0


def _parse_cost_per_action(
    cost_actions: list[dict] | None, key: str
) -> float:
    if not cost_actions:
        return 0.0
    for a in cost_actions:
        if a.get("action_type") == key:
            return float(a.get("value", 0))
    return 0.0


async def _upsert_metric(
    db: AsyncSession,
    ad: Ad,
    row: dict[str, Any],
) -> None:
    """Upsert one day of metrics for an ad."""
    date_str = row.get("date_start", "")
    if not date_str:
        return

    from datetime import datetime, timezone

    ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )

    # Check if row already exists
    existing = await db.execute(
        select(AdMetric).where(
            and_(
                AdMetric.ad_id == ad.id,
                AdMetric.timestamp == ts,
            )
        )
    )
    metric = existing.scalar_one_or_none()
    if metric is None:
        metric = AdMetric(
            ad_id=ad.id,
            account_id=ad.account_id,
            timestamp=ts,
        )
        db.add(metric)

    metric.account_id = ad.account_id
    metric.spend = float(row.get("spend", 0))
    metric.impressions = int(row.get("impressions", 0))
    metric.clicks = int(row.get("clicks", 0))
    metric.ctr = float(row.get("ctr", 0))
    metric.cpc = float(row.get("cpc", 0))
    metric.cpm = float(row.get("cpm", 0))
    metric.reach = int(row.get("reach", 0))
    metric.frequency = float(row.get("frequency", 0))

    actions = row.get("actions")
    cost_per = row.get("cost_per_action_type")
    metric.conversions = _parse_actions(actions, "lead")
    metric.cpl = _parse_cost_per_action(cost_per, "lead")
    metric.cpa = _parse_cost_per_action(
        cost_per, "offsite_conversion.fb_pixel_purchase"
    )


async def sync_metrics(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
    days_back: int = 30,
) -> int:
    """Pull ad-level daily insights and upsert into ad_metrics."""
    logger.info(
        "metrics_sync: starting for %s (last %d days)",
        meta_ad_account_id, days_back,
    )

    since = (date.today() - timedelta(days=days_back)).isoformat()
    until = date.today().isoformat()
    metric_count = 0

    # Build ad lookup: meta_ad_id → Ad
    ads_result = await db.execute(
        select(Ad).where(Ad.account_id == account_id)
    )
    ad_map: dict[str, Ad] = {}
    for ad in ads_result.scalars().all():
        if ad.meta_ad_id:
            ad_map[ad.meta_ad_id] = ad

    if not ad_map:
        logger.info("metrics_sync: no ads found, skipping")
        return 0

    # Fetch account-level insights broken down by ad per day
    try:
        async for page in meta_client.paginate(
            f"/{meta_ad_account_id}/insights",
            params={
                "fields": _INSIGHT_FIELDS,
                "level": "ad",
                "time_range": f'{{"since":"{since}","until":"{until}"}}',
                "time_increment": 1,
                "limit": 500,
            },
        ):
            for row in page.get("data", []):
                meta_ad_id = row.get("ad_id")
                ad = ad_map.get(meta_ad_id)
                if ad:
                    await _upsert_metric(db, ad, row)
                    metric_count += 1

            # Flush every page
            await db.flush()

    except Exception as exc:
        logger.error(
            "metrics_sync: failed for %s — %s",
            meta_ad_account_id, exc,
        )

    await db.commit()
    logger.info(
        "metrics_sync: done — %d metric rows for %s",
        metric_count, meta_ad_account_id,
    )
    return metric_count
