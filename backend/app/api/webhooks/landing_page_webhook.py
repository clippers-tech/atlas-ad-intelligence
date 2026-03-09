"""Landing page webhook — receives JS tracking snippet events."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.models.landing_page_event import LandingPageEvent
from app.schemas.webhook_schemas import LandingPageEventPayload

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/landing-page", status_code=status.HTTP_200_OK)
async def landing_page_webhook(
    payload: LandingPageEventPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive events from the landing page JS tracking snippet.
    Resolves account by slug and persists the event.
    """
    # Resolve account by slug
    result = await db.execute(
        select(Account).where(
            Account.slug == payload.account_slug,
            Account.is_active == True,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active account found for slug '{payload.account_slug}'.",
        )

    event = LandingPageEvent(
        account_id=account.id,
        page_url=payload.page_url,
        utm_campaign=payload.utm_campaign,
        utm_source=payload.utm_source,
        scroll_depth_percent=payload.scroll_depth_percent,
        time_on_page_seconds=payload.time_on_page_seconds,
        device_type=payload.device_type,
        browser=payload.browser,
    )
    db.add(event)
    await db.commit()

    logger.info(
        "Landing page event recorded account_id=%s url=%s scroll=%.0f%%",
        account.id,
        payload.page_url,
        payload.scroll_depth_percent or 0,
    )

    return {"status": "ok", "account_id": str(account.id)}
