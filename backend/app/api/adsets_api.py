"""Ad Sets API — list ad sets for an account."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ad_set import AdSet
from app.models.campaign import Campaign

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_ad_sets(
    account_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ad sets for a given account with campaign name."""
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
        data.append({
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
        })

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
