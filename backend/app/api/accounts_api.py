"""Accounts API — list, create, update ad accounts."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.schemas.account_schemas import AccountCreate, AccountResponse, AccountUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=dict)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
):
    """Return all active accounts."""
    result = await db.execute(
        select(Account).where(Account.is_active == True).order_by(Account.name)
    )
    accounts = result.scalars().all()
    return {
        "data": [AccountResponse.model_validate(a).model_dump() for a in accounts],
        "meta": {"total": len(accounts)},
    }


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new account."""
    # Check slug uniqueness
    existing = await db.execute(
        select(Account).where(Account.slug == payload.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Account with slug '{payload.slug}' already exists.",
        )

    account = Account(**payload.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    logger.info("Created account id=%s slug=%s", account.id, account.slug)
    return AccountResponse.model_validate(account)


@router.patch("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Partially update an account."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    await db.commit()
    await db.refresh(account)
    logger.info("Updated account id=%s", account_id)
    return AccountResponse.model_validate(account)
