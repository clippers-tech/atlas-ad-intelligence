"""Generic idempotency helpers — prevent duplicate event processing."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def check_and_mark_processed(
    event_type: str,
    event_id: str,
) -> bool:
    """Check whether an event has already been processed.

    Placeholder — returns False (not processed) for all events.
    Implement with a dedup table when needed.
    """
    logger.debug(
        "idempotency check: type=%s id=%s — allowing (no dedup store)",
        event_type,
        event_id,
    )
    return False
