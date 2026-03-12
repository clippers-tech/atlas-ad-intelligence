"""Sync Meta lead form submissions into ATLAS leads table.

Uses page-based approach: /{page_id}/leadgen_forms → /{form_id}/leads
Requires page access tokens stored on each account.

Deduplicates on meta_lead_id.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_set import AdSet
from app.models.campaign import Campaign
from app.models.lead import Lead

logger = logging.getLogger(__name__)

_LEAD_FIELDS = ",".join([
    "id", "created_time", "ad_id", "form_id",
    "field_data", "campaign_id", "adset_id",
])


def _extract_field(
    field_data: list[dict[str, Any]], name: str
) -> str | None:
    """Extract a value from Meta's field_data array."""
    for field in (field_data or []):
        if field.get("name") == name:
            vals = field.get("values", [])
            return vals[0] if vals else None
    return None


async def _resolve_attribution(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_campaign_id: str | None,
    meta_adset_id: str | None,
    meta_ad_id: str | None,
) -> dict:
    """Resolve Meta IDs to ATLAS UUIDs."""
    result = {
        "source_campaign_id": None,
        "source_adset_id": None,
        "source_ad_id": None,
    }
    if meta_campaign_id:
        row = await db.execute(
            select(Campaign.id).where(
                Campaign.meta_campaign_id == meta_campaign_id,
                Campaign.account_id == account_id,
            )
        )
        val = row.scalar_one_or_none()
        if val:
            result["source_campaign_id"] = val

    if meta_adset_id:
        row = await db.execute(
            select(AdSet.id).where(
                AdSet.meta_adset_id == meta_adset_id,
                AdSet.account_id == account_id,
            )
        )
        val = row.scalar_one_or_none()
        if val:
            result["source_adset_id"] = val

    if meta_ad_id:
        row = await db.execute(
            select(Ad.id).where(
                Ad.meta_ad_id == meta_ad_id,
                Ad.account_id == account_id,
            )
        )
        val = row.scalar_one_or_none()
        if val:
            result["source_ad_id"] = val
    return result


async def _upsert_lead(
    db: AsyncSession,
    account_id: uuid.UUID,
    raw: dict[str, Any],
) -> bool:
    """Upsert one lead from Meta data. Returns True if new."""
    meta_lead_id = raw.get("id")
    if not meta_lead_id:
        return False

    existing = await db.execute(
        select(Lead).where(Lead.meta_lead_id == meta_lead_id)
    )
    if existing.scalar_one_or_none():
        return False

    field_data = raw.get("field_data", [])
    email = _extract_field(field_data, "email")
    name = _extract_field(field_data, "full_name")
    phone = _extract_field(field_data, "phone_number")
    if not name:
        first = _extract_field(field_data, "first_name") or ""
        last = _extract_field(field_data, "last_name") or ""
        name = f"{first} {last}".strip() or None

    meta_created = None
    ts_str = raw.get("created_time")
    if ts_str:
        try:
            meta_created = datetime.fromisoformat(
                ts_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    attrib = await _resolve_attribution(
        db, account_id,
        raw.get("campaign_id"),
        raw.get("adset_id"),
        raw.get("ad_id"),
    )

    lead = Lead(
        account_id=account_id,
        meta_lead_id=meta_lead_id,
        meta_form_id=raw.get("form_id"),
        meta_ad_id=raw.get("ad_id"),
        email=email,
        name=name,
        phone=phone,
        stage="new",
        meta_created_at=meta_created,
        **attrib,
    )
    db.add(lead)
    return True
