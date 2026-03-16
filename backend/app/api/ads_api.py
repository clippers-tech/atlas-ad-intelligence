"""Ads API — list ads with date-filtered aggregated metrics."""

import json
import logging
from collections import defaultdict
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet

logger = logging.getLogger(__name__)
router = APIRouter()


def _date_filter(q, col, date_from, date_to):
    """Apply optional date range filter."""
    if date_from:
        q = q.where(col >= date_from)
    if date_to:
        q = q.where(col <= date_to)
    return q


def _merge_breakdowns(rows: list) -> list[dict]:
    """Merge conversion_breakdown JSON across days."""
    totals: dict[str, int] = defaultdict(int)
    for (bd_json,) in rows:
        if not bd_json:
            continue
        try:
            items = json.loads(bd_json)
            for item in items:
                totals[item["name"]] += item["value"]
        except (json.JSONDecodeError, KeyError):
            pass
    return [
        {"name": n, "value": v}
        for n, v in totals.items() if v > 0
    ]


async def _ad_metrics(
    db: AsyncSession,
    ad_id,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> dict:
    """Aggregate metrics for a single ad."""
    q = select(
        sa_func.coalesce(
            sa_func.sum(AdMetric.spend), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.impressions), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.link_clicks), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.conversions), 0),
        sa_func.coalesce(
            sa_func.sum(AdMetric.reach), 0),
    ).where(AdMetric.ad_id == ad_id)
    q = _date_filter(q, AdMetric.timestamp, date_from, date_to)
    row = (await db.execute(q)).one()
    s, imp, lc, conv, rch = (
        float(row[0]), int(row[1]), int(row[2]),
        int(row[3]), int(row[4]),
    )

    # Aggregate breakdown
    bd_q = select(
        AdMetric.conversion_breakdown,
    ).where(
        AdMetric.ad_id == ad_id,
        AdMetric.conversion_breakdown.isnot(None),
    )
    bd_q = _date_filter(
        bd_q, AdMetric.timestamp, date_from, date_to
    )
    bd_rows = (await db.execute(bd_q)).all()
    breakdown = _merge_breakdowns(bd_rows)

    cpr = round(s / conv, 2) if conv else 0.0
    return {
        "spend": round(s, 2), "impressions": imp,
        "reach": rch, "link_clicks": lc,
        "conversions": conv, "leads": conv,
        "cpm": (
            round(s / imp * 1000, 2) if imp else 0.0
        ),
        "cpc_link": round(s / lc, 2) if lc else 0.0,
        "ctr_link": (
            round(lc / imp * 100, 2) if imp else 0.0
        ),
        "cpl": cpr,
        "cost_per_result": cpr,
        "conversion_breakdown": (
            breakdown if breakdown else None
        ),
    }


@router.get("")
async def list_ads(
    account_id: str = Query(...),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List ads with date-filtered metrics."""
    spend_sq = (
        select(
            AdMetric.ad_id,
            sa_func.coalesce(
                sa_func.sum(AdMetric.spend), 0
            ).label("total_spend"),
        )
        .where(AdMetric.account_id == account_id)
    )
    spend_sq = _date_filter(
        spend_sq, AdMetric.timestamp,
        date_from, date_to,
    )
    spend_sq = (
        spend_sq.group_by(AdMetric.ad_id).subquery()
    )

    q = (
        select(Ad)
        .options(selectinload(Ad.ad_set))
        .outerjoin(
            spend_sq, Ad.id == spend_sq.c.ad_id
        )
        .where(Ad.account_id == account_id)
        .order_by(
            spend_sq.c.total_spend.desc().nullslast()
        )
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(Ad.id)).where(
                Ad.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for ad in rows:
        metrics = await _ad_metrics(
            db, ad.id, date_from, date_to
        )
        item = {
            "id": str(ad.id),
            "account_id": str(ad.account_id),
            "ad_set_id": str(ad.ad_set_id),
            "meta_ad_id": ad.meta_ad_id,
            "name": ad.name,
            "status": ad.status,
            "ad_type": ad.ad_type,
            "review_status": ad.review_status,
            "thumbnail_url": ad.thumbnail_url,
            "creative_url": ad.creative_url,
            "adset_name": (
                ad.ad_set.name if ad.ad_set else None
            ),
            "optimization_event": (
                ad.ad_set.optimization_event
                if ad.ad_set else None
            ),
            "created_at": ad.created_at.isoformat(),
            "updated_at": ad.updated_at.isoformat(),
        }
        item.update(metrics)
        data.append(item)

    return {
        "data": data,
        "meta": {
            "total": total,
            "page": 1,
            "per_page": limit,
        },
    }
