"""Campaigns API — list campaigns with aggregated ad metrics."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.campaign import Campaign
from app.schemas.campaign_schemas import CampaignResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# All metric columns we aggregate per campaign
_AGG_COLS = [
    ("spend", sa_func.sum, float),
    ("impressions", sa_func.sum, int),
    ("reach", sa_func.sum, int),
    ("link_clicks", sa_func.sum, int),
    ("clicks_all", sa_func.sum, int),
    ("landing_page_views", sa_func.sum, int),
    ("outbound_clicks", sa_func.sum, int),
    ("conversions", sa_func.sum, int),
    ("unique_clicks", sa_func.sum, int),
]


def _date_filter(q, col, date_from, date_to):
    """Apply optional date range filter."""
    if date_from:
        q = q.where(col >= date_from)
    if date_to:
        q = q.where(col <= date_to)
    return q


async def _campaign_metrics(
    db: AsyncSession,
    campaign_id: UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """Aggregate ad_metrics for a campaign within date range."""
    empty = {
        "spend": 0.0, "impressions": 0, "reach": 0,
        "link_clicks": 0, "clicks_all": 0,
        "landing_page_views": 0, "outbound_clicks": 0,
        "conversions": 0, "unique_clicks": 0,
        "cpm": 0.0, "cpc_link": 0.0, "cpc_all": 0.0,
        "ctr_link": 0.0, "ctr_all": 0.0,
        "cost_per_lpv": 0.0, "cpl": 0.0,
        "frequency": 0.0, "leads": 0, "roas": 0.0,
    }

    adset_ids = [
        r[0] for r in (
            await db.execute(
                select(AdSet.id).where(
                    AdSet.campaign_id == campaign_id
                )
            )
        ).all()
    ]
    if not adset_ids:
        return empty

    ad_ids = [
        r[0] for r in (
            await db.execute(
                select(Ad.id).where(Ad.ad_set_id.in_(adset_ids))
            )
        ).all()
    ]
    if not ad_ids:
        return empty

    q = select(
        sa_func.coalesce(sa_func.sum(AdMetric.spend), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.impressions), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.reach), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.link_clicks), 0),
        sa_func.coalesce(sa_func.sum(AdMetric.clicks_all), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.landing_page_views), 0
        ),
        sa_func.coalesce(
            sa_func.sum(AdMetric.outbound_clicks), 0
        ),
        sa_func.coalesce(sa_func.sum(AdMetric.conversions), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.unique_clicks), 0
        ),
    ).where(AdMetric.ad_id.in_(ad_ids))
    q = _date_filter(q, AdMetric.timestamp, date_from, date_to)
    row = (await db.execute(q)).one()

    s = float(row[0])
    imp = int(row[1])
    rch = int(row[2])
    lc = int(row[3])
    ca = int(row[4])
    lpv = int(row[5])
    oc = int(row[6])
    conv = int(row[7])
    uc = int(row[8])

    return {
        "spend": round(s, 2),
        "impressions": imp,
        "reach": rch,
        "link_clicks": lc,
        "clicks_all": ca,
        "landing_page_views": lpv,
        "outbound_clicks": oc,
        "conversions": conv,
        "unique_clicks": uc,
        "leads": conv,
        "cpm": round(s / imp * 1000, 2) if imp else 0.0,
        "cpc_link": round(s / lc, 2) if lc else 0.0,
        "cpc_all": round(s / ca, 2) if ca else 0.0,
        "ctr_link": round(lc / imp * 100, 2) if imp else 0.0,
        "ctr_all": round(ca / imp * 100, 2) if imp else 0.0,
        "cost_per_lpv": round(s / lpv, 2) if lpv else 0.0,
        "cpl": round(s / conv, 2) if conv else 0.0,
        "frequency": round(imp / rch, 2) if rch else 0.0,
        "roas": 0.0,
    }


@router.get("")
async def list_campaigns(
    account_id: str = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns enriched with date-filtered metrics."""
    q = (
        select(Campaign)
        .where(Campaign.account_id == account_id)
        .order_by(Campaign.name)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(Campaign.id)).where(
                Campaign.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for r in rows:
        item = CampaignResponse.model_validate(r).model_dump()
        metrics = await _campaign_metrics(
            db, r.id, date_from, date_to
        )
        item.update(metrics)
        data.append(item)

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
