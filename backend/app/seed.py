"""ATLAS seed script — creates initial accounts, rules, and seasonality configs.

Usage:
    python -m app.seed

Idempotent: safe to run multiple times. Existing records are left untouched.
"""

import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings
from app.models.account import Account
from app.seed_rules import seed_rules
from app.seed_seasonality import seed_seasonality


# ---------------------------------------------------------------------------
# Account definitions
# ---------------------------------------------------------------------------

ACCOUNTS = [
    {
        "name": "Lumina Web3",
        "slug": "lumina-web3",
        "business_type": "web3",
        "meta_ad_account_id": "1125463942968751",
        "target_cpl": 50.0,
        "target_cpa": 200.0,
        "target_roas": 3.0,
        "currency": "GBP",
        "timezone": "Europe/London",
    },
    {
        "name": "Lumina Clippers",
        "slug": "lumina-clippers",
        "business_type": "clippers",
        "meta_ad_account_id": "1103850885215983",
        "target_cpl": 30.0,
        "target_cpa": 120.0,
        "target_roas": 4.0,
        "currency": "GBP",
        "timezone": "Europe/London",
    },
    {
        "name": "OpenClaw Agency",
        "slug": "openclaw-agency",
        "business_type": "agency",
        "meta_ad_account_id": "986009306977380",
        "target_cpl": 60.0,
        "target_cpa": 250.0,
        "target_roas": 2.5,
        "currency": "GBP",
        "timezone": "Europe/London",
    },
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def get_or_create_account(session: AsyncSession, data: dict) -> tuple[Account, bool]:
    """Return (account, created). Looks up by slug; creates if absent."""
    result = await session.execute(
        select(Account).where(Account.slug == data["slug"])
    )
    account = result.scalars().first()
    if account is not None:
        return account, False

    account = Account(
        id=uuid.uuid4(),
        name=data["name"],
        slug=data["slug"],
        business_type=data["business_type"],
        meta_ad_account_id=data["meta_ad_account_id"],
        target_cpl=data["target_cpl"],
        target_cpa=data["target_cpa"],
        target_roas=data["target_roas"],
        currency=data["currency"],
        timezone=data["timezone"],
        is_active=True,
    )
    session.add(account)
    await session.flush()  # populate account.id without committing yet
    return account, True


# ---------------------------------------------------------------------------
# Main seed routine
# ---------------------------------------------------------------------------

async def run_seed() -> None:
    """Create all seed data inside a single transaction."""
    engine = create_async_engine(settings.database_url, future=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    print("=== ATLAS Seed Script ===")
    print(f"Database: {settings.database_url}\n")

    try:
        async with session_factory() as session:
            async with session.begin():
                for data in ACCOUNTS:
                    print(f"[account] Processing: {data['name']} ({data['slug']})")
                    account, created = await get_or_create_account(session, data)

                    if created:
                        print(f"  [account] Created account — id={account.id}")
                    else:
                        print(f"  [account] Already exists — id={account.id}, skipping creation.")

                    # Rules (12 per account)
                    await seed_rules(
                        session=session,
                        account_id=account.id,
                        account_name=account.name,
                        target_cpa=data["target_cpa"],
                        target_cpl=data["target_cpl"],
                        target_roas=data["target_roas"],
                    )

                    # Seasonality configs (12 months per account)
                    await seed_seasonality(
                        session=session,
                        account_id=account.id,
                        account_name=account.name,
                    )

                    print()

        print("=== Seed complete ===")

    except Exception as exc:
        print(f"\n[ERROR] Seed failed: {exc}")
        raise
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(run_seed())
