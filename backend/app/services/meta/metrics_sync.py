"""Sync Meta ad-level insights into ad_metrics table.

Pulls daily spend/impressions/clicks/conversions/landing-page-views
for each ad, upserting one row per ad per day.
"""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

# Fields requested from Meta Insights API
_INSIGHT_FIELDS = ",".join([
    "ad_id", "date_start",
    # Core
    "spend", "impressions", "reach", "frequency",
    # Click breakdown
    "inline_link_clicks",          # link clicks
    "clicks",                      # clicks (all)
    "inline_link_click_ctr",       # CTR (link)
    "website_ctr",                 # CTR (all) — array
    "cost_per_inline_link_click",  # CPC (link)
    "cost_per_unique_click",       # CPC (all)
    "cpm",
    # Outbound
    "outbound_clicks",
    # Conversions + cost
    "actions", "cost_per_action_type",
    # Unique
    "unique_clicks",
])


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


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _safe_float(val: Any) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _parse_outbound(row: dict) -> int:
    """outbound_clicks is an array of {action_type, value}."""
    oc = row.get("outbound_clicks")
    if not oc:
        return 0
    for item in oc:
        if item.get("action_type") == "outbound_click":
            return _safe_int(item.get("value", 0))
    return 0


def _parse_website_ctr(row: dict) -> float:
    """website_ctr is an array of {action_type, value}."""
    wc = row.get("website_ctr")
    if not wc:
        return 0.0
    for item in wc:
        if item.get("action_type") == "offsite_conversion.fb_pixel_view_content":
            return _safe_float(item.get("value", 0))
    # Fallback: first item
    if wc:
        return _safe_float(wc[0].get("value", 0))
    return 0.0


async def _upsert_metric(
    db: AsyncSession, ad: Ad, row: dict[str, Any],
) -> None:
    """Upsert one day of metrics for an ad."""
    date_str = row.get("date_start", "")
    if not date_str:
        return

    ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
        tzinfo=timezone.utc
    )

    existing = await db.execute(
        select(AdMetric).where(
            and_(AdMetric.ad_id == ad.id, AdMetric.timestamp == ts)
        )
    )
    metric = existing.scalar_one_or_none()
    if metric is None:
        metric = AdMetric(
            ad_id=ad.id, account_id=ad.account_id, timestamp=ts,
        )
        db.add(metric)

    metric.account_id = ad.account_id

    # Core
    metric.spend = _safe_float(row.get("spend"))
    metric.impressions = _safe_int(row.get("impressions"))
    metric.reach = _safe_int(row.get("reach"))
    metric.frequency = _safe_float(row.get("frequency"))
    metric.cpm = _safe_float(row.get("cpm"))

    # Clicks — link vs all
    metric.link_clicks = _safe_int(row.get("inline_link_clicks"))
    metric.clicks_all = _safe_int(row.get("clicks"))
    metric.clicks = metric.clicks_all  # legacy alias
    metric.ctr_link = _safe_float(row.get("inline_link_click_ctr"))
    metric.ctr_all = _parse_website_ctr(row)
    metric.ctr = metric.ctr_link  # legacy alias
    metric.cpc_link = _safe_float(row.get("cost_per_inline_link_click"))
    metric.cpc_all = _safe_float(row.get("cost_per_unique_click"))
    metric.cpc = metric.cpc_link  # legacy alias

    # Outbound
    metric.outbound_clicks = _parse_outbound(row)

    # Unique
    metric.unique_clicks = _safe_int(row.get("unique_clicks"))

    # Landing page views (in actions array)
    actions = row.get("actions")
    cost_per = row.get("cost_per_action_type")
    metric.landing_page_views = _parse_actions(
        actions, "landing_page_view"
    )
    metric.cost_per_lpv = _parse_cost_per_action(
        cost_per, "landing_page_view"
    )

    # Conversions
    metric.conversions = _parse_actions(actions, "lead")
    metric.cpl = _parse_cost_per_action(cost_per, "lead")
    metric.cost_per_result = metric.cpl  # same for lead campaigns
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

    try:
        async for page in meta_client.paginate(
            f"/{meta_ad_account_id}/insights",
            params={
                "fields": _INSIGHT_FIELDS,
                "level": "ad",
                "time_range": (
                    f'{{"since":"{since}","until":"{until}"}}'
                ),
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
