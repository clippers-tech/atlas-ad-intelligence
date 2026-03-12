"""Helper functions for Meta leadgen webhook processing.

Handles:
- Fetching full lead data using page access tokens
- Falling back to stub leads when fetch fails
- Resolving account from page_id or ad_id
"""

import logging
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.ad import Ad
from app.models.lead import Lead
from app.services.meta.leads_sync import (
    _resolve_attribution, _upsert_lead,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://graph.facebook.com/v21.0"
_LEAD_DETAIL_FIELDS = (
    "id,created_time,ad_id,form_id,"
    "field_data,campaign_id,adset_id"
)


async def process_leadgen_event(
    db: AsyncSession,
    leadgen_id: str,
    webhook_value: dict,
) -> bool:
    """Process one leadgen event. Returns True if new."""
    existing = await db.execute(
        select(Lead).where(
            Lead.meta_lead_id == leadgen_id
        )
    )
    if existing.scalar_one_or_none():
        logger.info("lead %s already exists", leadgen_id)
        return False

    # Resolve account + get page token
    account_id, page_token = await _resolve_account(
        db, webhook_value
    )
    if not account_id:
        logger.warning(
            "can't resolve account for lead %s",
            leadgen_id,
        )
        return False

    # Try full fetch using page token
    full_data = None
    if page_token:
        full_data = await _fetch_lead_with_page_token(
            leadgen_id, page_token
        )

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
) -> tuple:
    """Resolve (account_id, page_token) from webhook."""
    # Try ad_id first
    meta_ad_id = webhook_value.get("ad_id")
    if meta_ad_id:
        row = await db.execute(
            select(Ad.account_id).where(
                Ad.meta_ad_id == str(meta_ad_id)
            )
        )
        aid = row.scalar_one_or_none()
        if aid:
            acct = await db.execute(
                select(Account).where(Account.id == aid)
            )
            a = acct.scalar_one_or_none()
            if a:
                return a.id, a.meta_page_token

    # Try page_id
    page_id = webhook_value.get("page_id")
    if page_id:
        result = await db.execute(
            select(Account).where(
                Account.meta_page_id == str(page_id)
            )
        )
        a = result.scalar_one_or_none()
        if a:
            return a.id, a.meta_page_token

    return None, None


async def _fetch_lead_with_page_token(
    leadgen_id: str, page_token: str,
):
    """Fetch full lead via page token. None on failure."""
    try:
        async with httpx.AsyncClient(
            base_url=_BASE_URL, timeout=15.0
        ) as client:
            resp = await client.get(
                f"/{leadgen_id}",
                params={
                    "fields": _LEAD_DETAIL_FIELDS,
                    "access_token": page_token,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                logger.warning(
                    "Meta API error for %s: %s",
                    leadgen_id, data["error"],
                )
                return None
            logger.info(
                "fetched full lead %s via page token",
                leadgen_id,
            )
            return data
    except Exception as exc:
        logger.warning(
            "page token fetch failed for %s — %s",
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

    attrib = {}
    if meta_ad_id:
        attrib = await _resolve_attribution(
            db, account_id, None,
            webhook_value.get("adgroup_id"),
            str(meta_ad_id),
        )

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
        email=None, phone=None,
        stage="new",
        meta_created_at=meta_created,
        **attrib,
    )
    db.add(lead)
    logger.info("stored stub lead %s", leadgen_id)
    return True
