"""Dashboard overview — aggregate metrics for a date range."""

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


def _date_filter(q, col, date_from, date_to):
    if date_from:
        q = q.where(col >= date_from)
    if date_to:
        q = q.where(col <= date_to)
    return q


@router.get("/overview")
async def dashboard_overview(
    account_id: UUID = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """High-level KPIs and per-campaign breakdown."""

    # Aggregate all ad_metrics for this account + date range
    base = select(
        func.coalesce(func.sum(AdMetric.spend), 0),
        func.coalesce(func.sum(AdMetric.impressions), 0),
        func.coalesce(func.sum(AdMetric.reach), 0),
        func.coalesce(func.sum(AdMetric.link_clicks), 0),
        func.coalesce(func.sum(AdMetric.clicks_all), 0),
        func.coalesce(func.sum(AdMetric.landing_page_views), 0),
        func.coalesce(func.sum(AdMetric.conversions), 0),
    ).where(AdMetric.account_id == account_id)
    base = _date_filter(base, AdMetric.timestamp, date_from, date_to)

    totals = (await db.execute(base)).one()
    t_spend = float(totals[0])
    t_imp = int(totals[1])
    t_reach = int(totals[2])
    t_lc = int(totals[3])
    t_ca = int(totals[4])
    t_lpv = int(totals[5])
    t_conv = int(totals[6])

    # Leads from leads table
    lead_q = select(func.count(Lead.id)).where(
        Lead.account_id == account_id
    )
    lead_q = _date_filter(lead_q, Lead.created_at, date_from, date_to)
    total_leads = (await db.execute(lead_q)).scalar_one() or 0

    # Bookings
    bk_q = select(func.count(Booking.id)).where(
        Booking.account_id == account_id
    )
    bk_q = _date_filter(bk_q, Booking.created_at, date_from, date_to)
    total_bookings = (await db.execute(bk_q)).scalar_one() or 0

    # Revenue
    rev_q = select(func.sum(Deal.revenue)).where(
        Deal.account_id == account_id, Deal.stage == "closed_won"
    )
    rev_q = _date_filter(rev_q, Deal.closed_at, date_from, date_to)
    total_revenue = (await db.execute(rev_q)).scalar_one() or 0.0

    # Best available lead count: use DB leads if synced,
    # otherwise fall back to Meta conversion metrics
    effective_leads = max(total_leads, t_conv)
    avg_cpl = (
        round(t_spend / effective_leads, 2)
        if effective_leads else 0.0
    )
    true_roas = round(total_revenue / t_spend, 2) if t_spend else 0.0

    # Ad counts
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
    camps = (
        await db.execute(
            select(Campaign).where(Campaign.account_id == account_id)
        )
    ).scalars().all()
    breakdown = await _campaign_breakdown(
        db, account_id, camps, date_from, date_to
    )

    cost_per_result = (
        round(t_spend / t_conv, 2) if t_conv else 0.0
    )

    return {
        "data": {
            "total_spend": round(t_spend, 2),
            "total_impressions": t_imp,
            "total_reach": t_reach,
            "total_link_clicks": t_lc,
            "total_clicks_all": t_ca,
            "total_landing_page_views": t_lpv,
            "total_conversions": t_conv,
            "total_leads": total_leads,
            "effective_leads": effective_leads,
            "avg_cpl": avg_cpl,
            "cost_per_result": cost_per_result,
            "avg_cpm": round(t_spend / t_imp * 1000, 2) if t_imp else 0.0,
            "avg_cpc_link": round(t_spend / t_lc, 2) if t_lc else 0.0,
            "ctr_link": round(t_lc / t_imp * 100, 2) if t_imp else 0.0,
            "total_bookings": total_bookings,
            "total_revenue": round(total_revenue, 2),
            "true_roas": true_roas,
            "active_ads_count": active_ads,
            "paused_today_count": paused_ads,
            "campaigns": breakdown,
        }
    }


async def _campaign_breakdown(
    db, account_id, camps, date_from, date_to
) -> list[dict]:
    """Build per-campaign metric rows."""
    rows = []
    for camp in camps:
        adset_ids = [
            r[0] for r in (
                await db.execute(
                    select(AdSet.id).where(
                        AdSet.campaign_id == camp.id
                    )
                )
            ).all()
        ]
        cs, ci, clc, cca, clpv, ccv = 0.0, 0, 0, 0, 0, 0
        if adset_ids:
            ad_ids = [
                r[0] for r in (
                    await db.execute(
                        select(Ad.id).where(
                            Ad.ad_set_id.in_(adset_ids)
                        )
                    )
                ).all()
            ]
            if ad_ids:
                q = select(
                    func.coalesce(func.sum(AdMetric.spend), 0),
                    func.coalesce(func.sum(AdMetric.impressions), 0),
                    func.coalesce(func.sum(AdMetric.link_clicks), 0),
                    func.coalesce(func.sum(AdMetric.clicks_all), 0),
                    func.coalesce(
                        func.sum(AdMetric.landing_page_views), 0
                    ),
                    func.coalesce(func.sum(AdMetric.conversions), 0),
                ).where(AdMetric.ad_id.in_(ad_ids))
                q = _date_filter(
                    q, AdMetric.timestamp, date_from, date_to
                )
                r = (await db.execute(q)).one()
                cs = float(r[0])
                ci = int(r[1])
                clc = int(r[2])
                cca = int(r[3])
                clpv = int(r[4])
                ccv = int(r[5])

        cpr = round(cs / ccv, 2) if ccv else 0.0
        rows.append({
            "campaign_id": str(camp.id),
            "name": camp.name,
            "status": camp.status,
            "spend": round(cs, 2),
            "impressions": ci,
            "link_clicks": clc,
            "clicks_all": cca,
            "landing_page_views": clpv,
            "leads": ccv,
            "cpl": cpr,
            "cost_per_result": cpr,
            "cpm": round(cs / ci * 1000, 2) if ci else 0.0,
            "ctr_link": round(clc / ci * 100, 2) if ci else 0.0,
            "cpc_link": round(cs / clc, 2) if clc else 0.0,
            "bookings": 0,
            "revenue": 0.0,
            "roas": 0.0,
        })
    return rows
