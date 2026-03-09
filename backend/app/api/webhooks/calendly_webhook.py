"""Calendly webhook handler — ingest bookings and create Leads/Deals."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.models.booking import Booking
from app.models.deal import Deal
from app.models.lead import Lead
from app.schemas.webhook_schemas import CalendlyWebhookPayload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/calendly", status_code=status.HTTP_200_OK)
async def calendly_webhook(
    payload: CalendlyWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive Calendly webhook events.
    Supported events: invitee.created
    """
    event = payload.event
    data = payload.payload

    logger.info("Calendly webhook received: event=%s", event)

    if event not in ("invitee.created",):
        return {"status": "ignored", "event": event}

    # Extract invitee details
    invitee = data.get("invitee", {})
    invitee_email: str | None = invitee.get("email")
    invitee_name: str | None = invitee.get("name")
    calendly_event_id: str | None = data.get("event", data.get("uri", ""))

    if not calendly_event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing calendly event identifier.",
        )

    # Idempotency check
    existing_booking = await db.execute(
        select(Booking).where(Booking.calendly_event_id == calendly_event_id)
    )
    if existing_booking.scalar_one_or_none():
        logger.info("Duplicate Calendly event %s — skipping.", calendly_event_id)
        return {"status": "duplicate", "calendly_event_id": calendly_event_id}

    # Extract tracking/UTM
    tracking = data.get("tracking", {})
    utm_campaign = tracking.get("utm_campaign")
    utm_source = tracking.get("utm_source")
    utm_medium = tracking.get("utm_medium")
    utm_content = tracking.get("utm_content")
    utm_term = tracking.get("utm_term")

    # Resolve account — try to match by UTM campaign or fall back to first active
    account_result = await db.execute(
        select(Account).where(Account.is_active == True).limit(1)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No active account found to associate this booking.",
        )

    # Find or create Lead by email
    lead = None
    if invitee_email:
        lead_result = await db.execute(
            select(Lead).where(
                Lead.account_id == account.id,
                Lead.email == invitee_email,
            )
        )
        lead = lead_result.scalar_one_or_none()

    if not lead:
        lead = Lead(
            account_id=account.id,
            email=invitee_email,
            name=invitee_name,
            utm_campaign=utm_campaign,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_content=utm_content,
            utm_term=utm_term,
        )
        db.add(lead)
        await db.flush()  # get lead.id
        logger.info("Created new lead id=%s email=%s", lead.id, invitee_email)

    # Create Booking
    event_start_time = data.get("event_start_time")
    booked_at = None
    if event_start_time:
        try:
            booked_at = datetime.fromisoformat(event_start_time.replace("Z", "+00:00"))
        except ValueError:
            pass

    booking = Booking(
        lead_id=lead.id,
        account_id=account.id,
        calendly_event_id=calendly_event_id,
        event_type=data.get("event_type_name"),
        status="scheduled",
        booked_at=datetime.now(timezone.utc),
        event_at=booked_at,
    )
    db.add(booking)

    # Create Deal (only if lead has no open deal)
    existing_deal = await db.execute(
        select(Deal).where(
            Deal.lead_id == lead.id,
            Deal.stage.not_in(["closed_won", "closed_lost"]),
        )
    )
    if not existing_deal.scalar_one_or_none():
        deal = Deal(
            lead_id=lead.id,
            account_id=account.id,
            stage="new",
        )
        db.add(deal)

    await db.commit()
    logger.info("Calendly booking processed for lead id=%s", lead.id)

    return {"status": "ok", "lead_id": str(lead.id), "booking": calendly_event_id}
