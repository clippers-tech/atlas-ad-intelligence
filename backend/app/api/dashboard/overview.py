"""Dashboard overview — aggregate metrics across campaigns for a date range."""

import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.booking import Booking
from app.models.campaign import Campaign
from app.models.deal import Deal
from app.models.lead import Lead

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/overview")
async def dashboard_overview(
    account_id: UUID = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return high-level KPIs and per-campaign breakdown for the given date range."""

    # Build base metric query with optional date filters
    metric_q = select(
        AdMetric.ad_id,
        func.sum(AdMetric.spend).label("spend"),
        func.sum(AdMetric.clicks).label("clicks"),
        func.sum(AdMetric.conversions).label("conversions"),
    ).where(AdMetric.account_id == account_id)

    if date_from:
        metric_q = metric_q.where(AdMetric.timestamp >= date_from)
    if date_to:
        metric_q = metric_q.where(AdMetric.timestamp <= date_to)

    metric_q = metric_q.group_by(AdMetric.ad_id)
    metrics_result = await db.execute(metric_q)
    metrics_rows = metrics_result.all()

    total_spend = sum(r.spend for r in metrics_rows)
    total_clicks = sum(r.clicks for r in metrics_rows)

    # Leads count
    lead_q = select(func.count(Lead.id)).where(Lead.account_id == account_id)
    if date_from:
        lead_q = lead_q.where(Lead.created_at >= date_from)
    if date_to:
        lead_q = lead_q.where(Lead.created_at <= date_to)
    total_leads = (await db.execute(lead_q)).scalar_one() or 0

    # Bookings count
    booking_q = select(func.count(Booking.id)).where(Booking.account_id == account_id)
    if date_from:
        booking_q = booking_q.where(Booking.created_at >= date_from)
    if date_to:
        booking_q = booking_q.where(Booking.created_at <= date_to)
    total_bookings = (await db.execute(booking_q)).scalar_one() or 0

    # Revenue (closed_won deals)
    revenue_q = select(func.sum(Deal.revenue)).where(
        Deal.account_id == account_id, Deal.stage == "closed_won"
    )
    if date_from:
        revenue_q = revenue_q.where(Deal.closed_at >= date_from)
    if date_to:
        revenue_q = revenue_q.where(Deal.closed_at <= date_to)
    total_revenue = (await db.execute(revenue_q)).scalar_one() or 0.0

    avg_cpl = round(total_spend / total_leads, 2) if total_leads else 0.0
    true_roas = round(total_revenue / total_spend, 2) if total_spend else 0.0

    # Active / paused ad counts
    active_ads = (
        await db.execute(
            select(func.count(Ad.id)).where(
                Ad.account_id == account_id, Ad.status == "ACTIVE"
            )
        )
    ).scalar_one() or 0

    paused_ads = (
        await db.execute(
            select(func.count(Ad.id)).where(
                Ad.account_id == account_id, Ad.status == "PAUSED"
            )
        )
    ).scalar_one() or 0

    # Per-campaign breakdown
    campaigns_result = await db.execute(
        select(Campaign).where(Campaign.account_id == account_id)
    )
    campaigns = campaigns_result.scalars().all()
    campaign_breakdown = []
    for camp in campaigns:
        camp_spend = 0.0
        camp_leads = 0
        camp_bookings = 0
        camp_revenue = 0.0

        # Leads attributed to this campaign
        c_lead_q = select(func.count(Lead.id)).where(
            Lead.account_id == account_id,
            Lead.source_campaign_id == camp.id,
        )
        if date_from:
            c_lead_q = c_lead_q.where(Lead.created_at >= date_from)
        if date_to:
            c_lead_q = c_lead_q.where(Lead.created_at <= date_to)
        camp_leads = (await db.execute(c_lead_q)).scalar_one() or 0

        # Spend: sum ad_metrics for all ads in this campaign's ad_sets
        adset_ids_result = await db.execute(
            select(AdSet.id).where(AdSet.campaign_id == camp.id)
        )
        adset_ids = [r[0] for r in adset_ids_result.all()]
        if adset_ids:
            ad_ids_result = await db.execute(
                select(Ad.id).where(Ad.ad_set_id.in_(adset_ids))
            )
            ad_ids = [r[0] for r in ad_ids_result.all()]
            if ad_ids:
                camp_spend_q = select(func.sum(AdMetric.spend)).where(
                    AdMetric.ad_id.in_(ad_ids)
                )
                if date_from:
                    camp_spend_q = camp_spend_q.where(AdMetric.timestamp >= date_from)
                if date_to:
                    camp_spend_q = camp_spend_q.where(AdMetric.timestamp <= date_to)
                camp_spend = (await db.execute(camp_spend_q)).scalar_one() or 0.0

        # Revenue: closed_won deals from leads in this campaign
        c_rev_q = (
            select(func.sum(Deal.revenue))
            .join(Lead, Deal.lead_id == Lead.id)
            .where(Lead.source_campaign_id == camp.id, Deal.stage == "closed_won")
        )
        camp_revenue = (await db.execute(c_rev_q)).scalar_one() or 0.0
        camp_cpl = round(camp_spend / camp_leads, 2) if camp_leads else 0.0
        camp_roas = round(camp_revenue / camp_spend, 2) if camp_spend else 0.0

        campaign_breakdown.append({
            "campaign_id": str(camp.id),
            "name": camp.name,
            "status": camp.status,
            "spend": round(camp_spend, 2),
            "leads": camp_leads,
            "cpl": camp_cpl,
            "bookings": camp_bookings,
            "revenue": round(camp_revenue, 2),
            "roas": camp_roas,
        })

    return {
        "data": {
            "total_spend": round(total_spend, 2),
            "total_leads": total_leads,
            "avg_cpl": avg_cpl,
            "total_bookings": total_bookings,
            "total_revenue": round(total_revenue, 2),
            "true_roas": true_roas,
            "active_ads_count": active_ads,
            "paused_today_count": paused_ads,
            "campaigns": campaign_breakdown,
        }
    }
