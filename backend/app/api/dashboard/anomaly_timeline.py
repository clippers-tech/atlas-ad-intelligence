"""Dashboard anomaly timeline — detect metric deviations vs 7-day rolling average."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_metric import AdMetric

logger = logging.getLogger(__name__)
router = APIRouter()

DEVIATION_THRESHOLD = 0.30  # 30%
MONITORED_METRICS = ["spend", "ctr", "cpl", "cpc", "frequency"]


def _severity(deviation: float) -> str:
    if abs(deviation) >= 0.60:
        return "critical"
    if abs(deviation) >= 0.40:
        return "warning"
    return "info"


@router.get("/anomalies")
async def anomaly_timeline(
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare last 24h metrics against 7-day rolling average.
    Return any metric that deviates >30% as an anomaly.
    """
    now = datetime.now(timezone.utc)
    last_24h_start = now - timedelta(hours=24)
    rolling_start = now - timedelta(days=7)

    # Get all ads for this account
    ads_result = await db.execute(select(Ad).where(Ad.account_id == account_id))
    ads = ads_result.scalars().all()
    if not ads:
        return {"data": [], "meta": {"total": 0}}

    ad_ids = [ad.id for ad in ads]
    ad_name_map = {ad.id: ad.name for ad in ads}

    # Current 24h aggregates per ad
    current_q = (
        select(
            AdMetric.ad_id,
            func.avg(AdMetric.spend).label("spend"),
            func.avg(AdMetric.ctr).label("ctr"),
            func.avg(AdMetric.cpl).label("cpl"),
            func.avg(AdMetric.cpc).label("cpc"),
            func.avg(AdMetric.frequency).label("frequency"),
        )
        .where(
            AdMetric.ad_id.in_(ad_ids),
            AdMetric.timestamp >= last_24h_start,
        )
        .group_by(AdMetric.ad_id)
    )
    current_rows = {r.ad_id: r for r in (await db.execute(current_q)).all()}

    # 7-day rolling average per ad
    rolling_q = (
        select(
            AdMetric.ad_id,
            func.avg(AdMetric.spend).label("spend"),
            func.avg(AdMetric.ctr).label("ctr"),
            func.avg(AdMetric.cpl).label("cpl"),
            func.avg(AdMetric.cpc).label("cpc"),
            func.avg(AdMetric.frequency).label("frequency"),
        )
        .where(
            AdMetric.ad_id.in_(ad_ids),
            AdMetric.timestamp >= rolling_start,
            AdMetric.timestamp < last_24h_start,
        )
        .group_by(AdMetric.ad_id)
    )
    rolling_rows = {r.ad_id: r for r in (await db.execute(rolling_q)).all()}

    anomalies = []
    for ad_id, current in current_rows.items():
        rolling = rolling_rows.get(ad_id)
        if not rolling:
            continue

        for metric in MONITORED_METRICS:
            current_val = getattr(current, metric) or 0.0
            avg_val = getattr(rolling, metric) or 0.0

            if avg_val == 0:
                continue

            deviation = (current_val - avg_val) / avg_val

            if abs(deviation) >= DEVIATION_THRESHOLD:
                anomalies.append({
                    "ad_id": str(ad_id),
                    "ad_name": ad_name_map.get(ad_id, "Unknown"),
                    "metric": metric,
                    "current_value": round(current_val, 4),
                    "avg_value": round(avg_val, 4),
                    "deviation_percent": round(deviation * 100, 1),
                    "direction": "up" if deviation > 0 else "down",
                    "severity": _severity(deviation),
                    "timestamp": now.isoformat(),
                })

    # Sort by absolute deviation descending
    anomalies.sort(key=lambda x: abs(x["deviation_percent"]), reverse=True)

    return {
        "data": anomalies,
        "meta": {
            "total": len(anomalies),
            "window_hours": 24,
            "baseline_days": 7,
            "threshold_percent": DEVIATION_THRESHOLD * 100,
            "checked_at": now.isoformat(),
        },
    }
