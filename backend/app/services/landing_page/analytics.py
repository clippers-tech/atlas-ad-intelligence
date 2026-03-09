"""Landing page analytics — funnel metrics and top-page reporting."""

import logging
import uuid
from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.landing_page_event import LandingPageEvent
from app.models.lead import Lead

logger = logging.getLogger(__name__)

# Event type constants matching the LandingPageEvent.event_type values.
# LandingPageEvent doesn't have an explicit event_type column in the model,
# so we use utm_source as a proxy where event_type is not present.
# Actually, we use scroll_depth / time thresholds to infer funnel steps
# and the existing page_url + lead_id to count conversions.

# NOTE: LandingPageEvent has no event_type column in the model.
# We derive funnel steps from what's available:
#   - page_view  → any landing page event (all rows count as a page view)
#   - cta_click  → event where scroll_depth_percent >= 50 (engaged visitor)
#   - form_submit → event where lead_id IS NOT NULL (form was submitted → lead created)


async def get_funnel_metrics(
    db: AsyncSession,
    account_id: uuid.UUID,
    date_from: datetime,
    date_to: datetime,
) -> dict:
    """Aggregate landing page funnel metrics for the given date range.

    Funnel steps derived from LandingPageEvent:
    - page_views:   all events in range
    - cta_clicks:   events where scroll_depth_percent >= 50
    - form_submits: events where lead_id is not null
    - leads:        Lead rows created in range

    Returns conversion rates between consecutive funnel steps.
    """
    base_filter = [
        LandingPageEvent.account_id == account_id,
        LandingPageEvent.created_at >= date_from,
        LandingPageEvent.created_at <= date_to,
    ]

    counts_q = await db.execute(
        select(
            func.count().label("page_views"),
            func.count(
                case((LandingPageEvent.scroll_depth_percent >= 50, 1), else_=None)
            ).label("cta_clicks"),
            func.count(LandingPageEvent.lead_id).label("form_submits"),
        ).where(*base_filter)
    )
    row = counts_q.one()
    page_views: int = int(row.page_views)
    cta_clicks: int = int(row.cta_clicks)
    form_submits: int = int(row.form_submits)

    leads_q = await db.execute(
        select(func.count()).where(
            Lead.account_id == account_id,
            Lead.created_at >= date_from,
            Lead.created_at <= date_to,
        )
    )
    leads: int = int(leads_q.scalar_one())

    view_to_form_rate = round((form_submits / page_views * 100), 2) if page_views > 0 else 0.0
    form_to_lead_rate = round((leads / form_submits * 100), 2) if form_submits > 0 else 0.0

    logger.debug(
        "landing_page: account %s — views=%d cta=%d forms=%d leads=%d",
        account_id, page_views, cta_clicks, form_submits, leads,
    )

    return {
        "page_views": page_views,
        "cta_clicks": cta_clicks,
        "form_submits": form_submits,
        "leads": leads,
        "view_to_form_rate": view_to_form_rate,
        "form_to_lead_rate": form_to_lead_rate,
    }


async def get_top_landing_pages(
    db: AsyncSession,
    account_id: uuid.UUID,
    limit: int = 10,
) -> list[dict]:
    """Return the top landing pages ranked by conversion rate.

    Conversion = events where lead_id is set (form submitted).
    Pages with no URL are excluded.

    Each result includes:
    - page_url
    - total_events
    - conversions (events with an associated lead)
    - conversion_rate (%)
    """
    result = await db.execute(
        select(
            LandingPageEvent.page_url,
            func.count().label("total_events"),
            func.count(LandingPageEvent.lead_id).label("conversions"),
        )
        .where(
            LandingPageEvent.account_id == account_id,
            LandingPageEvent.page_url.isnot(None),
        )
        .group_by(LandingPageEvent.page_url)
        .order_by(
            (func.count(LandingPageEvent.lead_id) * 1.0 / func.count()).desc()
        )
        .limit(limit)
    )

    pages = []
    for row in result.all():
        total: int = int(row.total_events)
        conversions: int = int(row.conversions)
        conversion_rate = round((conversions / total * 100), 2) if total > 0 else 0.0
        pages.append({
            "page_url": row.page_url,
            "total_events": total,
            "conversions": conversions,
            "conversion_rate": conversion_rate,
        })

    logger.debug(
        "landing_page: account %s — top %d pages fetched", account_id, len(pages)
    )
    return pages
