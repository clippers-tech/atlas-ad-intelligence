"""Idempotency helpers — prevent duplicate processing of webhook events.

Strategy: check existing rows in bookings (calendly_event_id) and
payments (stripe_payment_id) rather than maintaining a separate table.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.payment import Payment

logger = logging.getLogger(__name__)


async def check_and_mark_processed(
    db: AsyncSession,
    event_type: str,
    event_id: str,
) -> bool:
    """Check whether a webhook event has already been processed.

    Args:
        db: Async database session.
        event_type: One of "calendly" or "stripe".
        event_id: The external unique ID (calendly_event_id or stripe_payment_id).

    Returns:
        True if the event was already processed (caller should skip).
        False if the event is new (caller should proceed).
    """
    event_type_lower = event_type.lower()

    if event_type_lower == "calendly":
        result = await db.execute(
            select(Booking.id).where(Booking.calendly_event_id == event_id).limit(1)
        )
        exists = result.scalar_one_or_none() is not None
        if exists:
            logger.info(
                "idempotency: calendly event %s already processed, skipping",
                event_id,
            )
        return exists

    if event_type_lower == "stripe":
        result = await db.execute(
            select(Payment.id).where(Payment.stripe_payment_id == event_id).limit(1)
        )
        exists = result.scalar_one_or_none() is not None
        if exists:
            logger.info(
                "idempotency: stripe payment %s already processed, skipping",
                event_id,
            )
        return exists

    logger.warning(
        "idempotency: unknown event_type %r — cannot check idempotency, allowing",
        event_type,
    )
    return False
