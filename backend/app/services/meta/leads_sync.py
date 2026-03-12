"""Sync Meta lead form submissions into ATLAS leads table.

Fetches lead data from Meta's Leadgen API at the ad-account level,
creates Lead records with full attribution (campaign → adset → ad).
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
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

# Fields to fetch for each lead
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

    # Check if already exists
    existing = await db.execute(
        select(Lead).where(Lead.meta_lead_id == meta_lead_id)
    )
    if existing.scalar_one_or_none():
        return False

    field_data = raw.get("field_data", [])
    email = _extract_field(field_data, "email")
    name = _extract_field(field_data, "full_name")
    phone = _extract_field(field_data, "phone_number")

    # Also try common alternate field names
    if not name:
        first = _extract_field(field_data, "first_name") or ""
        last = _extract_field(field_data, "last_name") or ""
        name = f"{first} {last}".strip() or None

    meta_ad_id = raw.get("ad_id")
    meta_campaign_id = raw.get("campaign_id")
    meta_adset_id = raw.get("adset_id")

    # Parse Meta timestamp
    meta_created = None
    ts_str = raw.get("created_time")
    if ts_str:
        try:
            meta_created = datetime.fromisoformat(
                ts_str.replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass

    # Resolve attribution
    attrib = await _resolve_attribution(
        db, account_id,
        meta_campaign_id, meta_adset_id, meta_ad_id,
    )

    lead = Lead(
        account_id=account_id,
        meta_lead_id=meta_lead_id,
        meta_form_id=raw.get("form_id"),
        meta_ad_id=meta_ad_id,
        email=email,
        name=name,
        phone=phone,
        stage="new",
        meta_created_at=meta_created,
        **attrib,
    )
    db.add(lead)
    return True


async def sync_leads(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
    days_back: int = 90,
) -> dict:
    """Pull leads from Meta Leadgen API for one account.

    Uses /{ad_account_id}/leadgen_forms to list forms, then
    /{form_id}/leads to get actual lead data.

    Returns dict with counts.
    """
    logger.info(
        "leads_sync: starting for %s (last %d days)",
        meta_ad_account_id, days_back,
    )

    new_count = 0
    skipped = 0
    form_count = 0
    errors = []

    try:
        # Step 1: Get all lead gen forms for this account
        async for form_page in meta_client.paginate(
            f"/{meta_ad_account_id}/leadgen_forms",
            params={"fields": "id,name,status", "limit": 100},
        ):
            for form in form_page.get("data", []):
                form_id = form.get("id")
                form_name = form.get("name", "?")
                form_count += 1

                logger.info(
                    "leads_sync: processing form %s (%s)",
                    form_id, form_name,
                )

                # Step 2: Get leads for this form
                try:
                    async for lead_page in meta_client.paginate(
                        f"/{form_id}/leads",
                        params={
                            "fields": _LEAD_FIELDS,
                            "limit": 500,
                        },
                    ):
                        for raw_lead in lead_page.get("data", []):
                            is_new = await _upsert_lead(
                                db, account_id, raw_lead
                            )
                            if is_new:
                                new_count += 1
                            else:
                                skipped += 1

                        await db.flush()

                except Exception as exc:
                    logger.warning(
                        "leads_sync: form %s failed — %s",
                        form_id, exc,
                    )
                    errors.append({
                        "form_id": form_id,
                        "form_name": form_name,
                        "error": str(exc),
                    })

    except Exception as exc:
        logger.error(
            "leads_sync: failed listing forms for %s — %s",
            meta_ad_account_id, exc,
        )
        errors.append({"error": str(exc)})

    await db.commit()

    result = {
        "forms_scanned": form_count,
        "new_leads": new_count,
        "skipped_existing": skipped,
        "errors": errors,
    }
    logger.info("leads_sync: done — %s", result)
    return result
