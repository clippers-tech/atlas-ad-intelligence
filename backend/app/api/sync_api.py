"""Trigger Meta data sync — campaigns, adsets, ads, then metrics."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.services.meta.campaigns_sync import sync_campaigns
from app.services.meta.metrics_sync import sync_metrics
from app.utils.circuit_breaker import meta_circuit, CircuitState

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/sync/trigger")
async def trigger_sync(
    account_id: UUID | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Pull campaigns + metrics from Meta for one or all accounts."""
    # For manual sync: temporarily raise the failure threshold so
    # individual 400s on specific adsets don't trip the breaker mid-sync
    from app.utils import circuit_breaker as cb_module
    original_threshold = cb_module._FAILURE_THRESHOLD
    cb_module._FAILURE_THRESHOLD = 50
    meta_circuit._state = CircuitState.CLOSED
    meta_circuit._failure_count = 0
    meta_circuit._opened_at = None
    if account_id:
        accounts_q = await db.execute(
            select(Account).where(Account.id == account_id, Account.is_active.is_(True))
        )
        accounts = [accounts_q.scalar_one_or_none()]
        if accounts[0] is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
    else:
        result = await db.execute(select(Account).where(Account.is_active.is_(True)))
        accounts = list(result.scalars().all())

    synced = []
    errors = []

    try:
        for acct in accounts:
            meta_id = f"act_{acct.meta_ad_account_id}"
            # Reset breaker between accounts so one bad account
            # doesn't block the next
            meta_circuit._failure_count = 0
            meta_circuit._state = CircuitState.CLOSED
            try:
                logger.info("sync_trigger: syncing %s (%s)", acct.name, meta_id)
                await sync_campaigns(db, acct.id, meta_id)
                await sync_metrics(db, acct.id, meta_id)
                synced.append({"account": acct.name, "status": "ok"})
            except Exception as exc:
                logger.error("sync_trigger: failed for %s — %s", acct.name, exc)
                errors.append({"account": acct.name, "error": str(exc)})
    finally:
        cb_module._FAILURE_THRESHOLD = original_threshold

    return {
        "data": {
            "synced": synced,
            "errors": errors,
            "total_accounts": len(accounts),
        }
    }
