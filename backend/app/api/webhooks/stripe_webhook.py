"""Stripe webhook handler — ingest payment events and update deals."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.deal import Deal
from app.models.lead import Lead
from app.models.payment import Payment
from app.schemas.webhook_schemas import StripeWebhookPayload

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_EVENTS = {"payment_intent.succeeded", "checkout.session.completed"}


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    payload: StripeWebhookPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive Stripe webhook events.
    On payment_intent.succeeded: record payment and close deal.
    """
    event_type = payload.type
    event_data = payload.data

    logger.info("Stripe webhook received: type=%s", event_type)

    if event_type not in SUPPORTED_EVENTS:
        return {"status": "ignored", "type": event_type}

    obj = event_data.get("object", {})

    # Extract payment details
    stripe_payment_id: str | None = obj.get("id")
    amount_received: int = obj.get("amount_received") or obj.get("amount_total") or 0
    currency: str = obj.get("currency", "gbp").upper()

    # Resolve customer email
    customer_email: str | None = None
    if "customer_details" in obj:
        customer_email = obj["customer_details"].get("email")
    elif "receipt_email" in obj:
        customer_email = obj.get("receipt_email")

    if not stripe_payment_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe payment id.",
        )

    # Idempotency check
    existing_payment = await db.execute(
        select(Payment).where(Payment.stripe_payment_id == stripe_payment_id)
    )
    if existing_payment.scalar_one_or_none():
        logger.info("Duplicate Stripe event %s — skipping.", stripe_payment_id)
        return {"status": "duplicate", "stripe_payment_id": stripe_payment_id}

    # Convert pence/cents to major currency unit
    amount_float = round(amount_received / 100, 2)

    # Find Lead by email
    lead = None
    deal = None
    if customer_email:
        lead_result = await db.execute(
            select(Lead).where(Lead.email == customer_email).limit(1)
        )
        lead = lead_result.scalar_one_or_none()

    if lead:
        deal_result = await db.execute(
            select(Deal)
            .where(Deal.lead_id == lead.id)
            .order_by(Deal.created_at.desc())
            .limit(1)
        )
        deal = deal_result.scalar_one_or_none()

    # We still record the payment even without a matched deal
    deal_id = deal.id if deal else None
    account_id = lead.account_id if lead else None

    if not account_id:
        logger.warning(
            "Stripe event %s: could not resolve account for email=%s",
            stripe_payment_id,
            customer_email,
        )
        return {"status": "unmatched", "stripe_payment_id": stripe_payment_id}

    # Create Payment record
    payment = Payment(
        deal_id=deal_id,
        account_id=account_id,
        stripe_payment_id=stripe_payment_id,
        amount=amount_float,
        currency=currency,
        payment_type="one_time",
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)

    # Update Deal to closed_won
    if deal and deal.stage not in ("closed_won", "closed_lost"):
        deal.stage = "closed_won"
        deal.revenue = amount_float
        deal.closed_at = datetime.now(timezone.utc)
        logger.info(
            "Deal id=%s closed_won revenue=%.2f %s", deal.id, amount_float, currency
        )

    await db.commit()
    logger.info(
        "Stripe payment %s processed, amount=%.2f %s", stripe_payment_id, amount_float, currency
    )

    return {
        "status": "ok",
        "stripe_payment_id": stripe_payment_id,
        "amount": amount_float,
        "currency": currency,
        "deal_id": str(deal_id) if deal_id else None,
    }
