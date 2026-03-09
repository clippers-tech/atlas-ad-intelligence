"""Seasonality config seed data for each ATLAS account.

Called by app.seed — not a standalone entry point.
"""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seasonality_config import SeasonalityConfig


# Monthly budget modifiers (percent) — positive = increase, negative = decrease.
# Rationale: Jan post-Christmas bounce, Nov Black-Friday run-up, Dec Q4 fatigue/budget exhaustion.
MONTHLY_MODIFIERS: dict[int, float] = {
    1:  20.0,   # January  — post-Christmas demand rebound
    2:   0.0,   # February — steady baseline
    3:  10.0,   # March    — spring uplift
    4:   0.0,   # April    — steady baseline
    5:   5.0,   # May      — mild pre-summer increase
    6:   0.0,   # June     — baseline
    7: -10.0,   # July     — summer slowdown
    8: -15.0,   # August   — peak holiday period, lower B2B conversions
    9:   5.0,   # September — back-to-business
    10: 10.0,   # October  — Q4 ramp-up
    11: 15.0,   # November — Black Friday / pre-Christmas peak
    12: -30.0,  # December — budgets exhausted, audience in holiday mode
}

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


async def seed_seasonality(session: AsyncSession, account_id: uuid.UUID, account_name: str) -> None:
    """Create 12 monthly SeasonalityConfig rows for an account.

    Idempotent — skips creation if any rows already exist for this account.
    """
    existing = await session.execute(
        select(SeasonalityConfig).where(SeasonalityConfig.account_id == account_id).limit(1)
    )
    if existing.scalars().first() is not None:
        print(f"  [seasonality] Configs already exist for {account_name} — skipping.")
        return

    configs = [
        SeasonalityConfig(
            id=uuid.uuid4(),
            account_id=account_id,
            month=month,
            budget_modifier_percent=modifier,
            notes=(
                f"{MONTH_NAMES[month]}: {'+' if modifier >= 0 else ''}{modifier:.0f}% budget modifier."
            ),
        )
        for month, modifier in MONTHLY_MODIFIERS.items()
    ]

    session.add_all(configs)
    await session.flush()
    print(f"  [seasonality] Created 12 monthly configs for {account_name}.")
