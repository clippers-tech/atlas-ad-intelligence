"""Alert router — looks up chat_id per account and dispatches Telegram messages."""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.account import Account
from app.services.notifications.telegram_client import telegram_client

logger = logging.getLogger(__name__)


async def _get_chat_id(db: AsyncSession, account_id: uuid.UUID) -> str:
    """Retrieve telegram_chat_id for an account, falling back to system default."""
    result = await db.execute(
        select(Account.telegram_chat_id).where(Account.id == account_id).limit(1)
    )
    chat_id = result.scalar_one_or_none()

    if chat_id:
        return chat_id

    fallback = settings.telegram_default_chat_id
    if fallback:
        logger.debug(
            "alert_router: account %s has no telegram_chat_id — using default %s",
            account_id,
            fallback,
        )
        return fallback

    logger.warning(
        "alert_router: no chat_id for account %s and no default configured",
        account_id,
    )
    return ""


async def route_alert(
    db: AsyncSession,
    account_id: uuid.UUID,
    alert_type: str,
    message: str,
) -> bool:
    """Route a formatted alert message to the correct Telegram chat.

    Args:
        db: Async database session (used to look up account's chat_id).
        account_id: ATLAS account UUID.
        alert_type: Descriptive label for logging (e.g. 'disapproved_ad', 'missed_task').
        message: Pre-formatted HTML string (use alert_formatter helpers).

    Returns:
        True if message was sent, False on error or missing chat_id.
    """
    chat_id = await _get_chat_id(db, account_id)

    if not chat_id:
        logger.error(
            "alert_router: cannot send %s alert for account %s — no chat_id available",
            alert_type,
            account_id,
        )
        return False

    logger.info(
        "alert_router: sending %s alert for account %s to chat %s",
        alert_type,
        account_id,
        chat_id,
    )
    return await telegram_client.send_message(chat_id=chat_id, text=message)


async def route_system_alert(message: str) -> bool:
    """Send a system-level alert to the default Telegram chat (no account lookup).

    Used for infrastructure alerts where no specific account is involved.
    """
    chat_id = settings.telegram_default_chat_id
    if not chat_id:
        logger.error("alert_router: no default telegram_chat_id for system alert")
        return False

    logger.info("alert_router: sending system alert to default chat %s", chat_id)
    return await telegram_client.send_message(chat_id=chat_id, text=message)
