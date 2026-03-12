"""Ad Sets API — list ad sets with aggregated metrics."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)
router = APIRouter()


async def _adset_metrics(
    db: AsyncSession, adset_id: UUID
) -> dict:
    """Aggregate all ad_metrics for an ad set."""
    empty = {
        "spend": 0.0, "impressions": 0, "reach": 0,
        "link_clicks": 0, "clicks_all": 0,
        "landing_page_views": 0, "conversions": 0,
        "unique_clicks": 0,
        "cpm": 0.0, "cpc_link": 0.0, "ctr_link": 0.0,
        "cost_per_lpv": 0.0, "cpl": 0.0,
        "leads": 0, "frequency": 0.0,
    }

    ad_ids = [
        r[0] for r in (
            await db.execute(
                select(Ad.id).where(Ad.ad_set_id == adset_id)
            )
        ).all()
    ]
    if not ad_ids:
        return empty

    row = (
        await db.execute(
            select(
                sa_func.coalesce(sa_func.sum(AdMetric.spend), 0),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.impressions), 0
                ),
                sa_func.coalesce(sa_func.sum(AdMetric.reach), 0),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.link_clicks), 0
                ),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.clicks_all), 0
                ),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.landing_page_views), 0
                ),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.conversions), 0
                ),
                sa_func.coalesce(
                    sa_func.sum(AdMetric.unique_clicks), 0
                ),
            ).where(AdMetric.ad_id.in_(ad_ids))
        )
    ).one()

    s = float(row[0])
    imp = int(row[1])
    rch = int(row[2])
    lc = int(row[3])
    ca = int(row[4])
    lpv = int(row[5])
    conv = int(row[6])
    uc = int(row[7])

    return {
        "spend": round(s, 2),
        "impressions": imp,
        "reach": rch,
        "link_clicks": lc,
        "clicks_all": ca,
        "landing_page_views": lpv,
        "conversions": conv,
        "unique_clicks": uc,
        "leads": conv,
        "cpm": round(s / imp * 1000, 2) if imp else 0.0,
        "cpc_link": round(s / lc, 2) if lc else 0.0,
        "ctr_link": round(lc / imp * 100, 2) if imp else 0.0,
        "cost_per_lpv": round(s / lpv, 2) if lpv else 0.0,
        "cpl": round(s / conv, 2) if conv else 0.0,
        "frequency": round(imp / rch, 2) if rch else 0.0,
    }


@router.get("")
async def list_ad_sets(
    account_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ad sets enriched with aggregated metrics."""
    q = (
        select(AdSet)
        .options(selectinload(AdSet.campaign))
        .where(AdSet.account_id == account_id)
        .order_by(AdSet.name)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(AdSet.id)).where(
                AdSet.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for r in rows:
        metrics = await _adset_metrics(db, r.id)
        item = {
            "id": str(r.id),
            "account_id": str(r.account_id),
            "campaign_id": str(r.campaign_id),
            "meta_adset_id": r.meta_adset_id,
            "name": r.name,
            "status": r.status,
            "audience_type": r.audience_type,
            "daily_budget": r.daily_budget,
            "campaign_name": (
                r.campaign.name if r.campaign else None
            ),
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
        }
        item.update(metrics)
        data.append(item)

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
