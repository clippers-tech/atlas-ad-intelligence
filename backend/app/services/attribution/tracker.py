"""Attribution tracker — links leads to ads and calculates ROAS."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.booking import Booking
from app.models.campaign import Campaign
from app.models.deal import Deal
from app.models.landing_page_event import LandingPageEvent
from app.models.lead import Lead
from app.models.payment import Payment

logger = logging.getLogger(__name__)


async def _best_ad_in_campaign(
    db: AsyncSession, account_id: uuid.UUID
) -> Ad | None:
    """Return the ad with the lowest average CPL for the account."""
    result = await db.execute(
        select(Ad.id, func.avg(AdMetric.cpl).label("avg_cpl"))
        .join(AdMetric, AdMetric.ad_id == Ad.id)
        .where(Ad.account_id == account_id, AdMetric.account_id == account_id, AdMetric.cpl > 0)
        .group_by(Ad.id)
        .order_by(func.avg(AdMetric.cpl).asc())
        .limit(1)
    )
    row = result.first()
    return await db.get(Ad, row.id) if row else None


async def attribute_lead(
    db: AsyncSession, lead_id: uuid.UUID
) -> dict | None:
    """Resolve attribution for a lead and return an attribution dict.

    Resolution order:
    1. source_ad_id already set → return existing attribution.
    2. utm_campaign set → match Campaign by name, pick best-performing ad.
    3. source_campaign_id set → pick best-performing ad in that campaign.
    """
    lead = await db.get(Lead, lead_id)
    if lead is None:
        logger.warning("attribution: lead %s not found", lead_id)
        return None

    if lead.source_ad_id:
        return {
            "ad_id": str(lead.source_ad_id),
            "campaign_id": str(lead.source_campaign_id) if lead.source_campaign_id else None,
            "adset_id": str(lead.source_adset_id) if lead.source_adset_id else None,
            "method": "existing",
        }

    campaign_id: uuid.UUID | None = lead.source_campaign_id

    if campaign_id is None and lead.utm_campaign:
        result = await db.execute(
            select(Campaign).where(
                Campaign.account_id == lead.account_id,
                Campaign.name.ilike(f"%{lead.utm_campaign}%"),
            ).limit(1)
        )
        campaign = result.scalar_one_or_none()
        if campaign:
            campaign_id = campaign.id

    if campaign_id is None:
        logger.debug("attribution: cannot resolve campaign for lead %s", lead_id)
        return None

    best_ad = await _best_ad_in_campaign(db, lead.account_id)
    if best_ad is None:
        return None

    lead.source_campaign_id = campaign_id
    lead.source_ad_id = best_ad.id
    lead.source_adset_id = best_ad.ad_set_id
    await db.flush()

    logger.info("attribution: lead %s attributed to ad %s", lead_id, best_ad.id)
    return {
        "ad_id": str(best_ad.id),
        "campaign_id": str(campaign_id),
        "adset_id": str(best_ad.ad_set_id),
        "method": "utm_match",
    }


async def calculate_roas(
    db: AsyncSession,
    account_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
) -> dict:
    """Calculate ROAS for the account over a date range.

    Returns total spend/revenue/ROAS plus a per-campaign breakdown.
    Spend sourced from AdMetric; revenue from closed_won Deals.
    """
    spend_q = await db.execute(
        select(func.coalesce(func.sum(AdMetric.spend), 0.0)).where(
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= date_from,
            AdMetric.timestamp <= date_to,
        )
    )
    total_spend: float = float(spend_q.scalar_one())

    revenue_q = await db.execute(
        select(func.coalesce(func.sum(Deal.revenue), 0.0)).where(
            Deal.account_id == account_id,
            Deal.stage == "closed_won",
            Deal.closed_at >= date_from,
            Deal.closed_at <= date_to,
        )
    )
    total_revenue: float = float(revenue_q.scalar_one())
    roas = (total_revenue / total_spend) if total_spend > 0 else 0.0

    # Per-campaign breakdown: join AdMetric → Ad → AdSet → Campaign
    camp_spend_q = await db.execute(
        select(Campaign.id, Campaign.name, func.coalesce(func.sum(AdMetric.spend), 0.0))
        .join(Ad.ad_set)
        .join(AdMetric, AdMetric.ad_id == Ad.id)
        .where(
            Campaign.account_id == account_id,
            AdMetric.timestamp >= date_from,
            AdMetric.timestamp <= date_to,
        )
        .group_by(Campaign.id, Campaign.name)
    )
    spend_by_campaign = {r[0]: (r[1], float(r[2])) for r in camp_spend_q.all()}

    camp_rev_q = await db.execute(
        select(Lead.source_campaign_id, func.coalesce(func.sum(Deal.revenue), 0.0))
        .join(Deal, Deal.lead_id == Lead.id)
        .where(
            Deal.account_id == account_id,
            Deal.stage == "closed_won",
            Deal.closed_at >= date_from,
            Deal.closed_at <= date_to,
            Lead.source_campaign_id.isnot(None),
        )
        .group_by(Lead.source_campaign_id)
    )
    rev_by_campaign = {r[0]: float(r[1]) for r in camp_rev_q.all()}

    by_campaign = []
    for camp_id, (camp_name, c_spend) in spend_by_campaign.items():
        c_revenue = rev_by_campaign.get(camp_id, 0.0)
        c_roas = (c_revenue / c_spend) if c_spend > 0 else 0.0
        by_campaign.append({
            "campaign_id": str(camp_id),
            "campaign_name": camp_name,
            "spend": c_spend,
            "revenue": c_revenue,
            "roas": round(c_roas, 4),
        })

    return {
        "total_spend": total_spend,
        "total_revenue": total_revenue,
        "roas": round(roas, 4),
        "by_campaign": by_campaign,
    }


async def get_lead_journey(
    db: AsyncSession, lead_id: uuid.UUID
) -> list[dict]:
    """Build a chronological journey timeline for a lead.

    Includes: lead created, landing page events, bookings, deals, payments.
    Returns list of step dicts sorted by timestamp ascending.
    """
    lead = await db.get(Lead, lead_id)
    if lead is None:
        logger.warning("attribution: lead %s not found for journey", lead_id)
        return []

    journey: list[dict] = [{
        "event": "lead_created",
        "timestamp": lead.created_at.isoformat(),
        "data": {"name": lead.name, "email": lead.email},
    }]

    lp_result = await db.execute(
        select(LandingPageEvent)
        .where(LandingPageEvent.lead_id == lead_id)
        .order_by(LandingPageEvent.created_at)
    )
    for ev in lp_result.scalars().all():
        journey.append({
            "event": "landing_page_event",
            "timestamp": ev.created_at.isoformat(),
            "data": {
                "page_url": ev.page_url,
                "scroll_depth_percent": ev.scroll_depth_percent,
                "time_on_page_seconds": ev.time_on_page_seconds,
            },
        })

    booking_result = await db.execute(
        select(Booking).where(Booking.lead_id == lead_id).order_by(Booking.booked_at)
    )
    for bk in booking_result.scalars().all():
        journey.append({
            "event": "booking",
            "timestamp": (bk.booked_at or bk.created_at).isoformat(),
            "data": {"event_type": bk.event_type, "status": bk.status},
        })

    deal_result = await db.execute(
        select(Deal).where(Deal.lead_id == lead_id).order_by(Deal.created_at)
    )
    for deal in deal_result.scalars().all():
        journey.append({
            "event": "deal",
            "timestamp": deal.created_at.isoformat(),
            "data": {"stage": deal.stage, "revenue": deal.revenue},
        })
        pay_result = await db.execute(
            select(Payment).where(Payment.deal_id == deal.id).order_by(Payment.paid_at)
        )
        for pay in pay_result.scalars().all():
            journey.append({
                "event": "payment",
                "timestamp": (pay.paid_at or pay.created_at).isoformat(),
                "data": {"amount": pay.amount, "currency": pay.currency},
            })

    journey.sort(key=lambda x: x["timestamp"])
    return journey
