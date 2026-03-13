"""Ads API — list ads with date-filtered aggregated metrics."""

import logging
from datetime import date
from typing import Optional

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


def _date_filter(q, col, date_from, date_to):
    """Apply optional date range filter."""
    if date_from:
        q = q.where(col >= date_from)
    if date_to:
        q = q.where(col <= date_to)
    return q


async def _ad_metrics(
    db: AsyncSession,
    ad_id,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """Aggregate metrics for a single ad within date range."""
    q = select(
        sa_func.coalesce(sa_func.sum(AdMetric.spend), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.impressions), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.link_clicks), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.conversions), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.reach), 0),
    ).where(AdMetric.ad_id == ad_id)
    q = _date_filter(q, AdMetric.timestamp, date_from, date_to)
    row = (await db.execute(q)).one()
    s, imp, lc, conv, rch = (
        float(row[0]), int(row[1]), int(row[2]),
        int(row[3]), int(row[4]),
    )
    return {
        "spend": round(s, 2), "impressions": imp,
        "reach": rch, "link_clicks": lc,
        "conversions": conv, "leads": conv,
        "cpm": round(s / imp * 1000, 2) if imp else 0.0,
        "cpc_link": round(s / lc, 2) if lc else 0.0,
        "ctr_link": round(lc / imp * 100, 2) if imp else 0.0,
        "cpl": round(s / conv, 2) if conv else 0.0,
    }


@router.get("")
async def list_ads(
    account_id: str = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ads with date-filtered metrics."""
    q = (
        select(Ad)
        .options(selectinload(Ad.ad_set))
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
        metrics = await _ad_metrics(
            db, ad.id, date_from, date_to
        )
        item = {
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
            "created_at": ad.created_at.isoformat(),
            "updated_at": ad.updated_at.isoformat(),
        }
        item.update(metrics)
        data.append(item)

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
