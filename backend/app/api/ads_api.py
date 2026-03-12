"""Ads API — list ads with aggregated metrics."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_ads(
    account_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ads with metrics and parent ad-set name."""
    q = (
        select(Ad)
        .options(
            selectinload(Ad.metrics),
            selectinload(Ad.ad_set),
        )
        .where(Ad.account_id == account_id)
        .order_by(Ad.name)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(Ad.id)).where(
                Ad.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for ad in rows:
        metrics = ad.metrics or []
        s = sum(m.spend for m in metrics)
        imp = sum(m.impressions for m in metrics)
        lc = sum(m.link_clicks for m in metrics)
        conv = sum(m.conversions for m in metrics)
        rch = sum(m.reach for m in metrics)

        data.append({
            "id": str(ad.id),
            "account_id": str(ad.account_id),
            "ad_set_id": str(ad.ad_set_id),
            "meta_ad_id": ad.meta_ad_id,
            "name": ad.name,
            "status": ad.status,
            "ad_type": ad.ad_type,
            "review_status": ad.review_status,
            "thumbnail_url": ad.thumbnail_url,
            "creative_url": ad.creative_url,
            "adset_name": (
                ad.ad_set.name if ad.ad_set else None
            ),
            "spend": round(s, 2),
            "impressions": imp,
            "reach": rch,
            "link_clicks": lc,
            "conversions": conv,
            "leads": conv,
            "cpm": round(s / imp * 1000, 2) if imp else 0.0,
            "cpc_link": round(s / lc, 2) if lc else 0.0,
            "ctr_link": (
                round(lc / imp * 100, 2) if imp else 0.0
            ),
            "cpl": round(s / conv, 2) if conv else 0.0,
            "created_at": ad.created_at.isoformat(),
            "updated_at": ad.updated_at.isoformat(),
        })

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
