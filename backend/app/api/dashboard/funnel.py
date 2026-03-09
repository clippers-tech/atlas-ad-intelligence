"""Dashboard funnel — full conversion funnel from click to revenue."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad_metric import AdMetric
from app.models.booking import Booking
from app.models.campaign import Campaign
from app.models.deal import Deal
from app.models.lead import Lead

logger = logging.getLogger(__name__)
router = APIRouter()


def _conversion_rate(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 1)


@router.get("/funnel")
async def funnel_view(
    account_id: UUID = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return funnel stage counts, conversion rates, and per-campaign breakdown."""

    # Clicks
    click_q = select(func.sum(AdMetric.clicks)).where(AdMetric.account_id == account_id)
    if date_from:
        click_q = click_q.where(AdMetric.timestamp >= date_from)
    if date_to:
        click_q = click_q.where(AdMetric.timestamp <= date_to)
    total_clicks = (await db.execute(click_q)).scalar_one() or 0

    # Leads (bookings = first conversion)
    lead_q = select(func.count(Lead.id)).where(Lead.account_id == account_id)
    if date_from:
        lead_q = lead_q.where(Lead.created_at >= date_from)
    if date_to:
        lead_q = lead_q.where(Lead.created_at <= date_to)
    total_leads = (await db.execute(lead_q)).scalar_one() or 0

    # Bookings
    book_q = select(func.count(Booking.id)).where(Booking.account_id == account_id)
    if date_from:
        book_q = book_q.where(Booking.created_at >= date_from)
    if date_to:
        book_q = book_q.where(Booking.created_at <= date_to)
    total_bookings = (await db.execute(book_q)).scalar_one() or 0

    # Calls completed (booking status = completed)
    calls_q = select(func.count(Booking.id)).where(
        Booking.account_id == account_id, Booking.status == "completed"
    )
    if date_from:
        calls_q = calls_q.where(Booking.created_at >= date_from)
    if date_to:
        calls_q = calls_q.where(Booking.created_at <= date_to)
    calls_completed = (await db.execute(calls_q)).scalar_one() or 0

    # Proposals sent
    proposals_q = select(func.count(Deal.id)).where(
        Deal.account_id == account_id, Deal.proposal_sent_at != None
    )
    proposals_sent = (await db.execute(proposals_q)).scalar_one() or 0

    # Closed won
    won_q = select(
        func.count(Deal.id), func.sum(Deal.revenue)
    ).where(Deal.account_id == account_id, Deal.stage == "closed_won")
    if date_from:
        won_q = won_q.where(Deal.closed_at >= date_from)
    if date_to:
        won_q = won_q.where(Deal.closed_at <= date_to)
    won_row = (await db.execute(won_q)).one()
    closed_won = won_row[0] or 0
    total_revenue = won_row[1] or 0.0

    stages = [
        {"stage": "clicks", "count": total_clicks, "cvr": None},
        {"stage": "leads", "count": total_leads, "cvr": _conversion_rate(total_leads, total_clicks)},
        {"stage": "bookings", "count": total_bookings, "cvr": _conversion_rate(total_bookings, total_leads)},
        {"stage": "calls_completed", "count": calls_completed, "cvr": _conversion_rate(calls_completed, total_bookings)},
        {"stage": "proposals_sent", "count": proposals_sent, "cvr": _conversion_rate(proposals_sent, calls_completed)},
        {"stage": "closed_won", "count": closed_won, "cvr": _conversion_rate(closed_won, proposals_sent)},
    ]

    # Per-campaign breakdown
    campaigns_result = await db.execute(
        select(Campaign).where(Campaign.account_id == account_id)
    )
    campaign_breakdown = []
    for camp in campaigns_result.scalars().all():
        c_leads = (
            await db.execute(
                select(func.count(Lead.id)).where(
                    Lead.account_id == account_id,
                    Lead.source_campaign_id == camp.id,
                )
            )
        ).scalar_one() or 0

        c_won = (
            await db.execute(
                select(func.count(Deal.id))
                .join(Lead, Deal.lead_id == Lead.id)
                .where(Lead.source_campaign_id == camp.id, Deal.stage == "closed_won")
            )
        ).scalar_one() or 0

        campaign_breakdown.append({
            "campaign_id": str(camp.id),
            "name": camp.name,
            "leads": c_leads,
            "closed_won": c_won,
            "close_rate": _conversion_rate(c_won, c_leads),
        })

    return {
        "data": {
            "stages": stages,
            "total_revenue": round(total_revenue, 2),
            "campaigns": campaign_breakdown,
        }
    }
