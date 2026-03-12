"""Meta Leadgen Webhook — real-time lead form submissions.

Meta sends a POST to this endpoint when a lead form is submitted.
The payload only contains the leadgen_id — we then call Meta's API
to fetch the actual lead data (name, email, phone).

Setup in Meta Business Manager:
  1. Go to Business Settings → Integrations → Leads Access
  2. Set webhook URL to: {BACKEND_URL}/api/webhooks/meta-leadgen
  3. Subscribe to 'leadgen' events
"""

import hashlib
import hmac
import logging

from fastapi import (
    APIRouter, Depends, HTTPException, Query,
    Request, status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.meta.leads_sync import (
    _resolve_attribution, _extract_field, _upsert_lead,
)
from app.services.meta.client import meta_client
from app.models.account import Account
from app.models.lead import Lead
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

# Fields to fetch when we get a leadgen_id
_LEAD_DETAIL_FIELDS = (
    "id,created_time,ad_id,form_id,"
    "field_data,campaign_id,adset_id"
)


@router.get("/meta-leadgen")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(
        None, alias="hub.verify_token"
    ),
):
    """Meta webhook verification handshake."""
    expected = settings.meta_webhook_verify_token
    if hub_mode == "subscribe" and hub_verify_token == expected:
        logger.info("Meta webhook verified.")
        return int(hub_challenge)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed.",
    )


@router.post("/meta-leadgen")
async def receive_leadgen(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Meta leadgen webhook events.

    Payload shape:
    {
      "entry": [{
        "id": "<page_id>",
        "time": 1234567890,
        "changes": [{
          "field": "leadgen",
          "value": {
            "leadgen_id": "...",
            "page_id": "...",
            "form_id": "...",
            "ad_id": "...",
            "adgroup_id": "...",
            "created_time": 1234567890
          }
        }]
      }]
    }
    """
    body = await request.json()
    entries = body.get("entry", [])

    new_leads = 0
    errors = []

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            if change.get("field") != "leadgen":
                continue

            value = change.get("value", {})
            leadgen_id = value.get("leadgen_id")
            if not leadgen_id:
                continue

            try:
                new = await _process_leadgen(
                    db, leadgen_id
                )
                if new:
                    new_leads += 1
            except Exception as exc:
                logger.error(
                    "leadgen webhook: failed for %s — %s",
                    leadgen_id, exc,
                )
                errors.append(str(exc))

    await db.commit()
    logger.info(
        "leadgen webhook: processed %d new leads, %d errors",
        new_leads, len(errors),
    )
    return {"status": "ok", "new_leads": new_leads}


async def _process_leadgen(
    db: AsyncSession, leadgen_id: str
) -> bool:
    """Fetch lead data from Meta and upsert."""
    # Check if already exists
    existing = await db.execute(
        select(Lead).where(Lead.meta_lead_id == leadgen_id)
    )
    if existing.scalar_one_or_none():
        return False

    # Fetch from Meta API
    data = await meta_client.get(
        f"/{leadgen_id}",
        params={"fields": _LEAD_DETAIL_FIELDS},
    )

    # Find which account this belongs to by matching
    # the ad_id to an ad in our DB
    meta_ad_id = data.get("ad_id")
    if not meta_ad_id:
        logger.warning(
            "leadgen webhook: no ad_id for lead %s",
            leadgen_id,
        )
        return False

    from app.models.ad import Ad
    ad_row = await db.execute(
        select(Ad).where(Ad.meta_ad_id == meta_ad_id)
    )
    ad = ad_row.scalar_one_or_none()
    if not ad:
        logger.warning(
            "leadgen webhook: ad %s not found in DB",
            meta_ad_id,
        )
        return False

    return await _upsert_lead(db, ad.account_id, data)
