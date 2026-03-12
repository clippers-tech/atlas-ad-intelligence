"""Page-based lead sync — pulls leads via page forms.

Flow: /{page_id}/leadgen_forms → /{form_id}/leads
Requires page access token per account.
"""

import logging
import uuid

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.meta.leads_sync import (
    _upsert_lead, _LEAD_FIELDS,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://graph.facebook.com/v21.0"


async def sync_leads_via_page(
    db: AsyncSession,
    account_id: uuid.UUID,
    page_id: str,
    page_token: str,
) -> dict:
    """Pull leads for one account via page leadgen forms.

    Returns summary dict with counts.
    """
    logger.info(
        "page_sync: starting for page %s", page_id
    )
    new_count = 0
    skipped = 0
    forms_checked = 0
    errors = []

    async with httpx.AsyncClient(
        base_url=_BASE_URL, timeout=30.0
    ) as client:
        forms_resp = await client.get(
            f"/{page_id}/leadgen_forms",
            params={
                "fields": "id,name,status,leads_count",
                "limit": "50",
                "access_token": page_token,
            },
        )
        forms_resp.raise_for_status()
        forms = forms_resp.json().get("data", [])
        logger.info(
            "page_sync: %d forms for page %s",
            len(forms), page_id,
        )

        for form in forms:
            lc = form.get("leads_count", 0)
            if not lc or int(lc) == 0:
                continue
            forms_checked += 1

            try:
                result = await _sync_form_leads(
                    client, db, account_id,
                    form["id"], page_token,
                )
                new_count += result["new"]
                skipped += result["skipped"]
            except Exception as exc:
                logger.error(
                    "page_sync: form %s err — %s",
                    form["id"], exc,
                )
                errors.append({
                    "form_id": form["id"],
                    "error": str(exc),
                })

    await db.commit()
    summary = {
        "method": "page_forms",
        "forms_total": len(forms),
        "forms_with_leads": forms_checked,
        "new_leads": new_count,
        "skipped_existing": skipped,
        "errors": errors,
    }
    logger.info("page_sync: done — %s", summary)
    return summary


async def _sync_form_leads(
    client: httpx.AsyncClient,
    db: AsyncSession,
    account_id: uuid.UUID,
    form_id: str,
    page_token: str,
) -> dict:
    """Fetch and upsert all leads from one form."""
    new = 0
    skipped = 0

    resp = await client.get(
        f"/{form_id}/leads",
        params={
            "fields": _LEAD_FIELDS,
            "limit": "500",
            "access_token": page_token,
        },
    )
    resp.raise_for_status()
    data = resp.json()

    while True:
        for raw in data.get("data", []):
            is_new = await _upsert_lead(
                db, account_id, raw
            )
            if is_new:
                new += 1
            else:
                skipped += 1
        await db.flush()

        next_url = data.get("paging", {}).get("next")
        if not next_url:
            break
        resp = await client.get(next_url)
        resp.raise_for_status()
        data = resp.json()

    return {"new": new, "skipped": skipped}
