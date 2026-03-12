"""Helper functions for Meta leadgen webhook processing.

Handles:
- Fetching full lead data from Meta API
- Falling back to stub leads when API fetch fails
- Resolving account from page_id or ad_id
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.ad import Ad
from app.models.lead import Lead
from app.services.meta.client import meta_client
from app.services.meta.leads_sync import (
    _resolve_attribution, _upsert_lead,
)

logger = logging.getLogger(__name__)

_LEAD_DETAIL_FIELDS = (
    "id,created_time,ad_id,form_id,"
    "field_data,campaign_id,adset_id"
)

# Known page-to-account mapping
_PAGE_ACCOUNT_MAP = {
    "835222503000847": "9e4163e5-7309-4978-b0be-bcbfe29d9788",
    "615112928357581": "4b6b46fa-73b5-4815-b049-4a76998b8d0f",
    "1049741201548167": "3a2cb8ff-7b74-44ac-ba07-594d1876b263",
}


async def process_leadgen_event(
    db: AsyncSession,
    leadgen_id: str,
    webhook_value: dict,
) -> bool:
    """Process one leadgen event. Returns True if new."""
    # Check duplicate
    existing = await db.execute(
        select(Lead).where(
            Lead.meta_lead_id == leadgen_id
        )
    )
    if existing.scalar_one_or_none():
        logger.info("lead %s already exists", leadgen_id)
        return False

    # Resolve account
    account_id = await _resolve_account(
        db, webhook_value
    )
    if not account_id:
        logger.warning(
            "can't resolve account for lead %s "
            "(ad=%s, page=%s)",
            leadgen_id,
            webhook_value.get("ad_id"),
            webhook_value.get("page_id"),
        )
        return False

    # Try full fetch from Meta API
    full_data = await _try_fetch_lead(leadgen_id)

    if full_data:
        return await _upsert_lead(
            db, account_id, full_data
        )

    # Fallback: stub lead from webhook payload
    return await _store_stub_lead(
        db, account_id, leadgen_id, webhook_value
    )


async def _resolve_account(
    db: AsyncSession, webhook_value: dict,
):
    """Resolve account_id from ad_id or page_id."""
    # Try ad_id first
    meta_ad_id = webhook_value.get("ad_id")
    if meta_ad_id:
        ad_row = await db.execute(
            select(Ad).where(
                Ad.meta_ad_id == str(meta_ad_id)
            )
        )
        ad = ad_row.scalar_one_or_none()
        if ad:
            return ad.account_id

    # Try page_id from known mapping
    page_id = webhook_value.get("page_id")
    if page_id:
        mapped = _PAGE_ACCOUNT_MAP.get(str(page_id))
        if mapped:
            return uuid.UUID(mapped)

        # DB fallback
        result = await db.execute(
            select(Account.id).where(
                Account.meta_page_id == str(page_id)
            )
        )
        return result.scalar_one_or_none()

    return None


async def _try_fetch_lead(leadgen_id: str):
    """Fetch full lead from Meta API. None on failure."""
    try:
        data = await meta_client.get(
            f"/{leadgen_id}",
            params={"fields": _LEAD_DETAIL_FIELDS},
        )
        logger.info("fetched full lead data for %s", leadgen_id)
        return data
    except Exception as exc:
        logger.warning(
            "Meta API fetch failed for %s — %s. "
            "Will store stub.",
            leadgen_id, exc,
        )
        return None


async def _store_stub_lead(
    db: AsyncSession,
    account_id,
    leadgen_id: str,
    webhook_value: dict,
) -> bool:
    """Store minimal lead from webhook payload."""
    meta_ad_id = webhook_value.get("ad_id")
    meta_form_id = webhook_value.get("form_id")

    # Resolve attribution
    attrib = {}
    if meta_ad_id:
        attrib = await _resolve_attribution(
            db, account_id,
            None,
            webhook_value.get("adgroup_id"),
            str(meta_ad_id),
        )

    # Parse unix timestamp
    meta_created = None
    ts = webhook_value.get("created_time")
    if ts:
        try:
            meta_created = datetime.fromtimestamp(
                int(ts), tz=timezone.utc
            )
        except (ValueError, TypeError):
            pass

    lead = Lead(
        account_id=account_id,
        meta_lead_id=leadgen_id,
        meta_form_id=(
            str(meta_form_id) if meta_form_id else None
        ),
        meta_ad_id=(
            str(meta_ad_id) if meta_ad_id else None
        ),
        name="[Pending — webhook stub]",
        email=None,
        phone=None,
        stage="new",
        meta_created_at=meta_created,
        **attrib,
    )
    db.add(lead)
    logger.info(
        "stored stub lead %s for account %s",
        leadgen_id, account_id,
    )
    return True
