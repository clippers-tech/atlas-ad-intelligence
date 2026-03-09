"""Deals API — list and update pipeline deals."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.deal import Deal
from app.schemas.deal_schemas import DealResponse, DealUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_deals(
    account_id: UUID = Query(...),
    stage: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Paginated deal list for an account, optionally filtered by stage."""
    base_q = select(Deal).where(Deal.account_id == account_id)
    count_q = select(func.count(Deal.id)).where(Deal.account_id == account_id)

    if stage:
        base_q = base_q.where(Deal.stage == stage)
        count_q = count_q.where(Deal.stage == stage)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * per_page
    rows = (
        await db.execute(
            base_q.order_by(Deal.created_at.desc()).offset(offset).limit(per_page)
        )
    ).scalars().all()

    return {
        "data": [DealResponse.model_validate(r).model_dump() for r in rows],
        "meta": {"total": total, "page": page, "per_page": per_page},
    }


@router.patch("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: UUID,
    payload: DealUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update deal stage, revenue, proposal date, close date, or notes."""
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deal not found.")

    update_data = payload.model_dump(exclude_unset=True)

    # Auto-set closed_at if stage moved to terminal states
    if "stage" in update_data and update_data["stage"] in ("closed_won", "closed_lost"):
        if not deal.closed_at and "closed_at" not in update_data:
            update_data["closed_at"] = datetime.now(timezone.utc)

    for field, value in update_data.items():
        setattr(deal, field, value)

    await db.commit()
    await db.refresh(deal)
    logger.info("Updated deal id=%s stage=%s", deal_id, deal.stage)
    return DealResponse.model_validate(deal)
