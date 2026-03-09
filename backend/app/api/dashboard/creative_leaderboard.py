"""Dashboard creative leaderboard — ranked ad performance with fatigue and placement data."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_placement_metric import AdPlacementMetric
from app.models.creative_metadata import CreativeMetadata

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_SORT_FIELDS = {"spend", "ctr", "cpl", "cpc", "frequency", "video_p100"}


@router.get("/creatives")
async def creative_leaderboard(
    account_id: UUID = Query(...),
    sort_by: str = Query("spend"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Return ranked creative performance, including fatigue status and placement breakdown."""

    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "spend"

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Aggregate metrics per ad
    metric_q = (
        select(
            AdMetric.ad_id,
            func.sum(AdMetric.spend).label("total_spend"),
            func.sum(AdMetric.clicks).label("total_clicks"),
            func.sum(AdMetric.impressions).label("total_impressions"),
            func.sum(AdMetric.conversions).label("total_conversions"),
            func.avg(AdMetric.ctr).label("avg_ctr"),
            func.avg(AdMetric.cpc).label("avg_cpc"),
            func.avg(AdMetric.cpl).label("avg_cpl"),
            func.avg(AdMetric.frequency).label("avg_frequency"),
            func.avg(AdMetric.video_p100).label("avg_video_p100"),
            func.avg(AdMetric.video_p75).label("avg_video_p75"),
            func.avg(AdMetric.video_view_3s_rate).label("avg_view_3s_rate"),
        )
        .where(AdMetric.account_id == account_id, AdMetric.timestamp >= since)
        .group_by(AdMetric.ad_id)
    )
    metric_rows = (await db.execute(metric_q)).all()
    metric_map = {r.ad_id: r for r in metric_rows}

    # Fetch ads for this account
    ads_result = await db.execute(select(Ad).where(Ad.account_id == account_id))
    ads = ads_result.scalars().all()

    # Placement breakdown per ad
    placement_q = (
        select(
            AdPlacementMetric.ad_id,
            AdPlacementMetric.placement,
            func.sum(AdPlacementMetric.spend).label("p_spend"),
            func.sum(AdPlacementMetric.clicks).label("p_clicks"),
            func.sum(AdPlacementMetric.conversions).label("p_conversions"),
        )
        .where(AdPlacementMetric.account_id == account_id, AdPlacementMetric.timestamp >= since)
        .group_by(AdPlacementMetric.ad_id, AdPlacementMetric.placement)
    )
    placement_rows = (await db.execute(placement_q)).all()

    placement_map: dict[UUID, list] = {}
    for p in placement_rows:
        placement_map.setdefault(p.ad_id, []).append({
            "placement": p.placement,
            "spend": round(p.p_spend, 2),
            "clicks": p.p_clicks,
            "conversions": p.p_conversions,
        })

    # Fetch creative metadata
    cm_result = await db.execute(
        select(CreativeMetadata).where(CreativeMetadata.account_id == account_id)
    )
    cm_map = {row.ad_id: row for row in cm_result.scalars().all()}

    items = []
    for ad in ads:
        m = metric_map.get(ad.id)
        cm = cm_map.get(ad.id)

        spend = round(m.total_spend, 2) if m else 0.0
        age_days = None
        if ad.first_active_date:
            age_days = (datetime.now(timezone.utc) - ad.first_active_date).days

        items.append({
            "ad_id": str(ad.id),
            "name": ad.name,
            "status": ad.status,
            "ad_type": ad.ad_type,
            "thumbnail_url": ad.thumbnail_url,
            "spend": spend,
            "ctr": round(m.avg_ctr, 4) if m else 0.0,
            "cpc": round(m.avg_cpc, 2) if m else 0.0,
            "cpl": round(m.avg_cpl, 2) if m else 0.0,
            "frequency": round(m.avg_frequency, 2) if m else 0.0,
            "video_p100": round(m.avg_video_p100, 4) if m else 0.0,
            "video_p75": round(m.avg_video_p75, 4) if m else 0.0,
            "video_view_3s_rate": round(m.avg_view_3s_rate, 4) if m else 0.0,
            "is_fatigued": cm.is_fatigued if cm else False,
            "hook_type": cm.hook_type if cm else None,
            "format": cm.format if cm else None,
            "age_days": age_days,
            "placements": placement_map.get(ad.id, []),
        })

    # Sort
    reverse = order == "desc"
    items.sort(key=lambda x: x.get(sort_by, 0) or 0, reverse=reverse)
    for rank, item in enumerate(items, 1):
        item["rank"] = rank

    return {"data": items, "meta": {"total": len(items), "sort_by": sort_by, "order": order}}
