"""Campaigns API — list campaigns with aggregated spend metrics."""

import logging
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


async def _campaign_spend(
    db: AsyncSession, campaign_id: UUID
) -> dict:
    """Sum spend + conversions for a campaign via adsets→ads→ad_metrics."""
    adset_ids = [
        r[0]
        for r in (
            await db.execute(
                select(AdSet.id).where(AdSet.campaign_id == campaign_id)
            )
        ).all()
    ]
    if not adset_ids:
        return {"spend": 0.0, "leads": 0, "cpl": 0.0, "roas": 0.0}

    ad_ids = [
        r[0]
        for r in (
            await db.execute(
                select(Ad.id).where(Ad.ad_set_id.in_(adset_ids))
            )
        ).all()
    ]
    if not ad_ids:
        return {"spend": 0.0, "leads": 0, "cpl": 0.0, "roas": 0.0}

    row = (
        await db.execute(
            select(
                sa_func.coalesce(sa_func.sum(AdMetric.spend), 0),
                sa_func.coalesce(sa_func.sum(AdMetric.conversions), 0),
            ).where(AdMetric.ad_id.in_(ad_ids))
        )
    ).one()

    spend = float(row[0])
    leads = int(row[1])
    cpl = round(spend / leads, 2) if leads else 0.0
    return {"spend": round(spend, 2), "leads": leads, "cpl": cpl, "roas": 0.0}


@router.get("")
async def list_campaigns(
    account_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns for a given account, enriched with spend metrics."""
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
        metrics = await _campaign_spend(db, r.id)
        item.update(metrics)
        data.append(item)

    return {"data": data, "meta": {"total": total, "page": 1, "per_page": limit}}
