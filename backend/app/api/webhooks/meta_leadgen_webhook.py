"""Meta Leadgen Webhook — real-time lead form submissions.

Meta sends a POST with leadgen_id — we fetch the actual
lead data from Meta API. If fetch fails (permissions),
we store a stub lead from the webhook payload.
"""

import logging

from fastapi import (
    APIRouter, Depends, HTTPException, Query,
    Request, status,
)
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models.lead import Lead
from app.api.webhooks.leadgen_helpers import (
    process_leadgen_event,
)

logger = logging.getLogger(__name__)
router = APIRouter()


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
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed.",
    )


@router.post("/meta-leadgen")
async def receive_leadgen(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Meta leadgen webhook events."""
    body = await request.json()
    logger.info("leadgen webhook: payload=%s", body)
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
                new = await process_leadgen_event(
                    db, leadgen_id, value
                )
                if new:
                    new_leads += 1
            except Exception as exc:
                logger.error(
                    "leadgen webhook: failed %s — %s",
                    leadgen_id, exc, exc_info=True,
                )
                errors.append(str(exc))

    await db.commit()
    logger.info(
        "leadgen webhook: %d new, %d errors",
        new_leads, len(errors),
    )
    return {
        "status": "ok",
        "new_leads": new_leads,
        "errors": errors,
    }
