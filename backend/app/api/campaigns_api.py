"""Campaigns API — list campaigns for an account."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.campaign import Campaign
from app.schemas.campaign_schemas import CampaignResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_campaigns(
    account_id: str = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List campaigns for a given account."""
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

    return {
        "data": [
            CampaignResponse.model_validate(r).model_dump()
            for r in rows
        ],
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
