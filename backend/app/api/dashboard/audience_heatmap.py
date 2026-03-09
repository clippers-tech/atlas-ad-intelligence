"""Dashboard audience heatmap — audience performance, CPL matrix, saturation alerts."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.audience_test_queue import AudienceTestQueue
from app.models.deal import Deal
from app.models.lead import Lead

logger = logging.getLogger(__name__)
router = APIRouter()

SATURATION_FREQUENCY_THRESHOLD = 3.5


@router.get("/audiences")
async def audience_heatmap(
    account_id: UUID = Query(...),
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Return audience performance data, CPL heatmap matrix, and saturation alerts."""

    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Get all ad sets for this account
    adsets_result = await db.execute(
        select(AdSet).where(AdSet.account_id == account_id)
    )
    adsets = adsets_result.scalars().all()
    adset_map = {adset.id: adset for adset in adsets}

    # Aggregate metrics per ad_set (via Ad → AdMetric)
    # First get ad→adset mapping
    ads_result = await db.execute(select(Ad).where(Ad.account_id == account_id))
    ads = ads_result.scalars().all()
    ad_to_adset = {ad.id: ad.ad_set_id for ad in ads}

    metric_q = (
        select(
            AdMetric.ad_id,
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.conversions).label("conversions"),
            func.avg(AdMetric.frequency).label("frequency"),
            func.avg(AdMetric.cpl).label("cpl"),
        )
        .where(AdMetric.account_id == account_id, AdMetric.timestamp >= since)
        .group_by(AdMetric.ad_id)
    )
    metric_rows = (await db.execute(metric_q)).all()

    # Aggregate by adset
    adset_metrics: dict[UUID, dict] = {}
    for m in metric_rows:
        adset_id = ad_to_adset.get(m.ad_id)
        if not adset_id:
            continue
        if adset_id not in adset_metrics:
            adset_metrics[adset_id] = {"spend": 0.0, "conversions": 0, "frequency": [], "cpl": []}
        adset_metrics[adset_id]["spend"] += m.spend or 0
        adset_metrics[adset_id]["conversions"] += m.conversions or 0
        adset_metrics[adset_id]["frequency"].append(m.frequency or 0)
        adset_metrics[adset_id]["cpl"].append(m.cpl or 0)

    # Get leads count per adset
    leads_by_adset: dict[UUID, int] = {}
    for adset in adsets:
        lead_q = select(func.count(Lead.id)).where(
            Lead.account_id == account_id,
            Lead.source_adset_id == str(adset.id),
        )
        count = (await db.execute(lead_q)).scalar_one() or 0
        leads_by_adset[adset.id] = count

    # Close rate per adset (won / leads)
    close_rate_by_adset: dict[UUID, float] = {}
    for adset_id, leads_count in leads_by_adset.items():
        if leads_count:
            won_q = (
                select(func.count(Deal.id))
                .join(Lead, Deal.lead_id == Lead.id)
                .where(
                    Lead.source_adset_id == str(adset_id),
                    Deal.stage == "closed_won",
                )
            )
            won = (await db.execute(won_q)).scalar_one() or 0
            close_rate_by_adset[adset_id] = round(won / leads_count * 100, 1)
        else:
            close_rate_by_adset[adset_id] = 0.0

    # Build audience list
    audience_list = []
    saturation_alerts = []

    for adset in adsets:
        m = adset_metrics.get(adset.id, {})
        spend = round(m.get("spend", 0.0), 2)
        leads = leads_by_adset.get(adset.id, 0)
        avg_freq = round(sum(m.get("frequency", [0])) / max(len(m.get("frequency", [1])), 1), 2)
        avg_cpl = round(sum(m.get("cpl", [0])) / max(len(m.get("cpl", [1])), 1), 2)

        row = {
            "adset_id": str(adset.id),
            "name": adset.name,
            "audience_type": adset.audience_type,
            "spend": spend,
            "leads": leads,
            "cpl": avg_cpl,
            "frequency": avg_freq,
            "close_rate": close_rate_by_adset.get(adset.id, 0.0),
        }
        audience_list.append(row)

        if avg_freq >= SATURATION_FREQUENCY_THRESHOLD:
            saturation_alerts.append({
                "adset_id": str(adset.id),
                "name": adset.name,
                "frequency": avg_freq,
                "message": f"Frequency {avg_freq} exceeds threshold {SATURATION_FREQUENCY_THRESHOLD}",
            })

    # Audience type comparison
    type_comparison: dict[str, dict] = {}
    for row in audience_list:
        atype = row["audience_type"]
        if atype not in type_comparison:
            type_comparison[atype] = {"spend": 0.0, "leads": 0, "count": 0, "cpl_sum": 0.0}
        type_comparison[atype]["spend"] += row["spend"]
        type_comparison[atype]["leads"] += row["leads"]
        type_comparison[atype]["count"] += 1
        type_comparison[atype]["cpl_sum"] += row["cpl"]

    type_data = [
        {
            "audience_type": k,
            "total_spend": round(v["spend"], 2),
            "total_leads": v["leads"],
            "avg_cpl": round(v["cpl_sum"] / v["count"], 2) if v["count"] else 0.0,
        }
        for k, v in type_comparison.items()
    ]

    # Test queue
    test_q_result = await db.execute(
        select(AudienceTestQueue)
        .where(AudienceTestQueue.account_id == account_id)
        .order_by(AudienceTestQueue.created_at.desc())
        .limit(20)
    )
    test_queue = [
        {"id": str(r.id), "name": r.audience_name, "type": r.audience_type, "status": r.status}
        for r in test_q_result.scalars().all()
    ]

    return {
        "data": {
            "audiences": audience_list,
            "type_comparison": type_data,
            "test_queue": test_queue,
            "saturation_alerts": saturation_alerts,
        }
    }
