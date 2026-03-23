"""Aggregate daily ad-metric rows into per-ad totals for rule evaluation.

Volume metrics (spend, impressions, clicks, etc.) are summed.
Rate metrics (CPM, CTR, CPC, CPL, CPA, etc.) are recalculated from
the summed components so they are mathematically accurate.
"""

import uuid
from dataclasses import dataclass, field

from app.models.ad_metric import AdMetric

# How far back to look at daily metric rows (days).
EVAL_WINDOW_DAYS = 7

# Metrics that should be summed across the window.
_SUM_METRICS = {
    "spend", "impressions", "reach", "link_clicks", "clicks",
    "clicks_all", "conversions", "leads", "outbound_clicks",
    "landing_page_views", "unique_clicks",
}


@dataclass
class AggregatedMetrics:
    """Holds summed / averaged metrics for one ad."""

    ad_id: uuid.UUID
    values: dict[str, float] = field(default_factory=dict)

    def get(self, name: str) -> float | None:
        return self.values.get(name)


def aggregate_rows(rows: list[AdMetric]) -> AggregatedMetrics:
    """Aggregate a list of daily metric rows for one ad."""
    if not rows:
        raise ValueError("Cannot aggregate empty list")

    ad_id = rows[0].ad_id
    agg = AggregatedMetrics(ad_id=ad_id)

    # Sum volume metrics
    for key in _SUM_METRICS:
        total = 0.0
        for r in rows:
            v = getattr(r, key, None)
            if v is not None:
                total += float(v)
        agg.values[key] = total

    # Recalculate rate metrics from summed components
    spend = agg.values.get("spend", 0)
    imps = agg.values.get("impressions", 0)
    link_clicks = agg.values.get("link_clicks", 0)
    clicks_all = agg.values.get("clicks_all", 0)
    conversions = agg.values.get("conversions", 0)
    leads = agg.values.get("leads", 0)
    lpv = agg.values.get("landing_page_views", 0)
    reach = agg.values.get("reach", 0)

    agg.values["cpm"] = (spend / imps * 1000) if imps else 0
    agg.values["cpc_link"] = (spend / link_clicks) if link_clicks else 0
    agg.values["cpc"] = agg.values["cpc_link"]
    agg.values["cpc_all"] = (spend / clicks_all) if clicks_all else 0
    agg.values["ctr_link"] = (
        (link_clicks / imps * 100) if imps else 0
    )
    agg.values["ctr"] = agg.values["ctr_link"]
    agg.values["ctr_all"] = (
        (clicks_all / imps * 100) if imps else 0
    )
    agg.values["cpl"] = (spend / leads) if leads else 0
    agg.values["cpa"] = (spend / conversions) if conversions else 0
    agg.values["cost_per_result"] = agg.values["cpa"]
    agg.values["cost_per_lpv"] = (spend / lpv) if lpv else 0
    agg.values["frequency"] = (imps / reach) if reach else 0
    agg.values["roas"] = 0  # placeholder — no revenue data yet

    return agg
