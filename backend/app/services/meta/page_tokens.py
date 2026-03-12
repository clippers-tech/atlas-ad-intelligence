"""Manage Meta Page Access Tokens.

Page tokens are required for:
- Fetching leadgen forms (/{page_id}/leadgen_forms)
- Fetching individual leads (/{leadgen_id})
- Reading lead form submissions

Tokens are refreshed by calling /me/accounts with the
system user token, which returns page tokens for all
connected pages.
"""

import logging
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.account import Account
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)


async def refresh_page_tokens(
    db: AsyncSession,
) -> dict[str, Any]:
    """Refresh page tokens for all ATLAS accounts.

    Calls /me/accounts to get fresh page tokens,
    then updates the accounts table.
    """
    # Fetch all pages the user token has access to
    data = await meta_client.get(
        "/me/accounts",
        params={
            "fields": "id,name,access_token",
            "limit": "50",
        },
    )
    pages = data.get("data", [])
    logger.info(
        "page_tokens: found %d pages from /me/accounts",
        len(pages),
    )

    # Build page_id -> token map
    token_map = {
        p["id"]: p["access_token"]
        for p in pages
        if p.get("access_token")
    }

    # Get all ATLAS accounts with page IDs
    result = await db.execute(
        select(Account).where(
            Account.meta_page_id.isnot(None),
            Account.is_active.is_(True),
        )
    )
    accounts = result.scalars().all()

    updated = []
    missing = []

    for account in accounts:
        page_id = account.meta_page_id
        if page_id in token_map:
            account.meta_page_token = token_map[page_id]
            updated.append(account.name)
        else:
            missing.append(
                f"{account.name} (page {page_id})"
            )

    await db.commit()

    summary = {
        "pages_from_meta": len(pages),
        "accounts_updated": updated,
        "accounts_missing": missing,
    }
    logger.info("page_tokens: refresh done — %s", summary)
    return summary


async def get_page_token(
    db: AsyncSession, account_id,
) -> str | None:
    """Get page token for an account. None if not set."""
    result = await db.execute(
        select(Account.meta_page_token).where(
            Account.id == account_id
        )
    )
    return result.scalar_one_or_none()


async def get_page_token_by_page_id(
    db: AsyncSession, page_id: str,
) -> str | None:
    """Get page token by Meta page ID."""
    result = await db.execute(
        select(Account.meta_page_token).where(
            Account.meta_page_id == page_id
        )
    )
    return result.scalar_one_or_none()
