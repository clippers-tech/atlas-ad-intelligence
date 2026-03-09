"""Sync Meta ad insights (metrics) into ad_metrics and ad_placement_metrics tables."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_placement_metric import AdPlacementMetric
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

_INSIGHT_FIELDS = (
    "ad_id,spend,impressions,clicks,ctr,cpc,cpm,actions,"
    "frequency,video_p25_watched_actions,video_p50_watched_actions,"
    "video_p75_watched_actions,video_p100_watched_actions,reach,unique_clicks"
)


def _parse_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _extract_action_value(actions: list[dict], action_type: str) -> int:
    for action in (actions or []):
        if action.get("action_type") == action_type:
            return _parse_int(action.get("value", 0))
    return 0


def _extract_video_pct(video_actions: list[dict] | None, pct: str) -> float:
    for entry in (video_actions or []):
        if entry.get("action_type") == f"video_view_p{pct}":
            return _parse_float(entry.get("value", 0.0))
    return 0.0


async def _get_or_none_ad_id(db: AsyncSession, meta_ad_id: str) -> uuid.UUID | None:
    result = await db.execute(select(Ad.id).where(Ad.meta_ad_id == meta_ad_id).limit(1))
    return result.scalar_one_or_none()


async def _store_ad_metric(
    db: AsyncSession,
    account_id: uuid.UUID,
    ad_id: uuid.UUID,
    row: dict[str, Any],
    ts: datetime,
) -> None:
    actions = row.get("actions") or []
    metric = AdMetric(
        ad_id=ad_id,
        account_id=account_id,
        timestamp=ts,
        spend=_parse_float(row.get("spend")),
        impressions=_parse_int(row.get("impressions")),
        clicks=_parse_int(row.get("clicks")),
        ctr=_parse_float(row.get("ctr")),
        cpc=_parse_float(row.get("cpc")),
        cpm=_parse_float(row.get("cpm")),
        conversions=_extract_action_value(actions, "lead"),
        frequency=_parse_float(row.get("frequency")),
        video_p25=_extract_video_pct(row.get("video_p25_watched_actions"), "25"),
        video_p50=_extract_video_pct(row.get("video_p50_watched_actions"), "50"),
        video_p75=_extract_video_pct(row.get("video_p75_watched_actions"), "75"),
        video_p100=_extract_video_pct(row.get("video_p100_watched_actions"), "100"),
        reach=_parse_int(row.get("reach")),
        unique_clicks=_parse_int(row.get("unique_clicks")),
    )
    db.add(metric)


async def _store_placement_metrics(
    db: AsyncSession,
    account_id: uuid.UUID,
    ad_id: uuid.UUID,
    placement_rows: list[dict[str, Any]],
    ts: datetime,
) -> None:
    for row in placement_rows:
        placement = row.get("publisher_platform", "other")
        pm = AdPlacementMetric(
            ad_id=ad_id,
            account_id=account_id,
            timestamp=ts,
            placement=placement,
            spend=_parse_float(row.get("spend")),
            impressions=_parse_int(row.get("impressions")),
            clicks=_parse_int(row.get("clicks")),
            ctr=_parse_float(row.get("ctr")),
            conversions=_extract_action_value(row.get("actions") or [], "lead"),
        )
        db.add(pm)


async def sync_metrics(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
) -> None:
    """Fetch insights and store ad-level + placement-level metrics."""
    ts = datetime.now(tz=timezone.utc)
    logger.info("metrics_sync: starting for account %s (%s)", account_id, meta_ad_account_id)
    count = 0

    async for page in meta_client.paginate(
        f"/{meta_ad_account_id}/insights",
        params={
            "level": "ad",
            "fields": _INSIGHT_FIELDS,
            "breakdowns": "publisher_platform",
            "limit": 100,
        },
    ):
        rows_by_ad: dict[str, list[dict]] = {}
        for row in page.get("data", []):
            meta_ad_id = row.get("ad_id", "")
            rows_by_ad.setdefault(meta_ad_id, []).append(row)

        for meta_ad_id, rows in rows_by_ad.items():
            ad_id = await _get_or_none_ad_id(db, meta_ad_id)
            if ad_id is None:
                logger.debug("metrics_sync: no local ad for meta_ad_id %s, skipping", meta_ad_id)
                continue
            # Store aggregate (first row has aggregate, rest are placement breakdowns)
            await _store_ad_metric(db, account_id, ad_id, rows[0], ts)
            await _store_placement_metrics(db, account_id, ad_id, rows, ts)
            count += 1

    await db.commit()
    logger.info("metrics_sync: stored metrics for %d ads, account %s", count, account_id)
