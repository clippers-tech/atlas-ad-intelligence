"""Creatives Performance API — metrics with fatigue + ad set context."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.creative_metadata import CreativeMetadata

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/performance")
async def creative_performance(
    account_id: str = Query(...),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return creative-level performance with fatigue."""
    q = (
        select(Ad)
        .options(
            selectinload(Ad.creative_metadata),
            selectinload(Ad.metrics),
            selectinload(Ad.ad_set),
        )
        .where(Ad.account_id == account_id)
        .order_by(Ad.name)
        .limit(limit)
    )
    result = await db.execute(q)
    ads = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(Ad.id)).where(
                Ad.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for ad in ads:
        metrics = ad.metrics or []
        total_spend = sum(m.spend for m in metrics)
        total_impr = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conv = sum(m.conversions for m in metrics)
        avg_ctr = (
            (total_clicks / total_impr * 100)
            if total_impr > 0 else 0.0
        )

        cm = ad.creative_metadata
        age_days = 0
        if ad.first_active_date:
            age_days = (
                datetime.now(timezone.utc) - ad.first_active_date
            ).days

        fatigue = "fresh"
        if age_days > 21:
            fatigue = "fatigued"
        elif age_days > 10:
            fatigue = "declining"
        if cm and cm.is_fatigued:
            fatigue = "fatigued"

        adset_name = ad.ad_set.name if ad.ad_set else None

        data.append({
            "id": str(ad.id),
            "ad_id": str(ad.id),
            "ad_name": ad.name,
            "adset_name": adset_name,
            "ad_type": ad.ad_type,
            "thumbnail_url": ad.thumbnail_url,
            "status": ad.status,
            "spend": round(total_spend, 2),
            "impressions": total_impr,
            "ctr": round(avg_ctr, 2),
            "conversions": total_conv,
            "fatigue_level": fatigue,
            "age_days": age_days,
            "hook_type": cm.hook_type if cm else None,
            "cta_type": cm.cta_type if cm else None,
            "placements": [],
        })

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
