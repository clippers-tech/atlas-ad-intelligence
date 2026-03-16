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
from app.models.ad_set import AdSet
from app.services.meta.client import meta_client
from app.services.meta.metrics_parsers import (
    _safe_int, _safe_float,
    parse_actions, parse_cost_per_action,
    parse_outbound, parse_website_ctr,
    parse_results_and_breakdown, parse_result_cost,
)

logger = logging.getLogger(__name__)

# Fields requested from Meta Insights API
_INSIGHT_FIELDS = ",".join([
    "ad_id", "date_start",
    # Core
    "spend", "impressions", "reach", "frequency",
    # Click breakdown
    "inline_link_clicks",
    "clicks",
    "inline_link_click_ctr",
    "website_ctr",
    "cost_per_inline_link_click",
    "cost_per_unique_click",
    "cpm",
    # Outbound
    "outbound_clicks",
    # Conversions + cost
    "actions", "cost_per_action_type",
    # Unique
    "unique_clicks",
])


async def _upsert_metric(
    db: AsyncSession, ad: Ad, row: dict[str, Any],
    meta_ad_account_id: str = "",
    optimization_event: str | None = None,
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

    # Core
    metric.spend = _safe_float(row.get("spend"))
    metric.impressions = _safe_int(row.get("impressions"))
    metric.reach = _safe_int(row.get("reach"))
    metric.frequency = _safe_float(row.get("frequency"))
    metric.cpm = _safe_float(row.get("cpm"))

    # Clicks — link vs all
    metric.link_clicks = _safe_int(
        row.get("inline_link_clicks")
    )
    metric.clicks_all = _safe_int(row.get("clicks"))
    metric.clicks = metric.clicks_all
    metric.ctr_link = _safe_float(
        row.get("inline_link_click_ctr")
    )
    metric.ctr_all = parse_website_ctr(row)
    metric.ctr = metric.ctr_link
    metric.cpc_link = _safe_float(
        row.get("cost_per_inline_link_click")
    )
    metric.cpc_all = _safe_float(
        row.get("cost_per_unique_click")
    )
    metric.cpc = metric.cpc_link

    # Outbound
    metric.outbound_clicks = parse_outbound(row)

    # Unique
    metric.unique_clicks = _safe_int(
        row.get("unique_clicks")
    )

    # Landing page views (in actions array)
    actions = row.get("actions")
    cost_per = row.get("cost_per_action_type")
    metric.landing_page_views = parse_actions(
        actions, "landing_page_view"
    )
    metric.cost_per_lpv = parse_cost_per_action(
        cost_per, "landing_page_view"
    )

    # Conversions / Results — per ad-set optimization
    results, breakdown_json = parse_results_and_breakdown(
        actions, meta_ad_account_id, optimization_event,
    )
    metric.conversions = results
    metric.conversion_breakdown = breakdown_json
    metric.cost_per_result = parse_result_cost(
        metric.spend, results, cost_per,
    )
    metric.cpl = metric.cost_per_result
    metric.cpa = parse_cost_per_action(
        cost_per,
        "offsite_conversion.fb_pixel_purchase",
    )


async def sync_metrics(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
    days_back: int = 30,
) -> int:
    """Pull ad-level daily insights and upsert."""
    logger.info(
        "metrics_sync: starting for %s (last %d days)",
        meta_ad_account_id, days_back,
    )

    since = (
        date.today() - timedelta(days=days_back)
    ).isoformat()
    until = date.today().isoformat()
    metric_count = 0

    # Build ad_id → Ad map + ad_id → optimization_event
    ads_result = await db.execute(
        select(Ad).where(Ad.account_id == account_id)
    )
    ad_map: dict[str, Ad] = {}
    for ad in ads_result.scalars().all():
        if ad.meta_ad_id:
            ad_map[ad.meta_ad_id] = ad

    if not ad_map:
        logger.info("metrics_sync: no ads found, skip")
        return 0

    # Build ad_set_id → optimization_event lookup
    adset_ids = {ad.ad_set_id for ad in ad_map.values()}
    adset_result = await db.execute(
        select(
            AdSet.id, AdSet.optimization_event,
        ).where(AdSet.id.in_(adset_ids))
    )
    opt_map: dict[uuid.UUID, str | None] = {
        row[0]: row[1] for row in adset_result.all()
    }

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
                    opt_evt = opt_map.get(
                        ad.ad_set_id
                    )
                    await _upsert_metric(
                        db, ad, row,
                        meta_ad_account_id, opt_evt,
                    )
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
