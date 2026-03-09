"""Market conditions service — BTC price tracking, seasonality, and market summaries."""

import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.market_condition import MarketCondition
from app.models.seasonality_config import SeasonalityConfig

logger = logging.getLogger(__name__)

_BTC_CHANGE_THRESHOLD = 0.05  # 5% price swing triggers a new MarketCondition record
_MARKET_SUMMARY_DAYS = 30
_HTTP_TIMEOUT = 10.0


async def check_btc_price(db: AsyncSession) -> dict[str, Any]:
    """Fetch the current BTC price and compare against the last stored value.

    Uses settings.btc_price_api_url (CoinGecko by default).
    Creates a new MarketCondition row if price has moved >5% since last check
    or if no prior record exists for today.

    Returns:
        Dict with current_price, previous_price, change_pct, and significant (bool).
    """
    current_price = await _fetch_btc_price()
    if current_price is None:
        logger.error("checker: failed to fetch BTC price — aborting")
        return {
            "current_price": None,
            "previous_price": None,
            "change_pct": None,
            "significant": False,
        }

    # Get the most recent stored MarketCondition
    prev_result = await db.execute(
        select(MarketCondition)
        .order_by(MarketCondition.date.desc())
        .limit(1)
    )
    previous = prev_result.scalar_one_or_none()
    previous_price: float | None = previous.btc_price if previous else None

    change_pct: float | None = None
    significant = False

    if previous_price and previous_price > 0:
        change_pct = (current_price - previous_price) / previous_price
        significant = abs(change_pct) >= _BTC_CHANGE_THRESHOLD

    today = date.today()
    should_record = significant or previous is None or previous.date != today

    if should_record:
        condition = MarketCondition(
            date=today,
            btc_price=current_price,
            btc_7d_change_percent=round(change_pct * 100, 2) if change_pct is not None else None,
            is_btc_crash=(change_pct is not None and change_pct < -_BTC_CHANGE_THRESHOLD),
        )
        db.add(condition)
        await db.commit()
        logger.info(
            "checker: stored new MarketCondition — price=%.2f change=%.2f%%",
            current_price,
            (change_pct * 100) if change_pct is not None else 0.0,
        )

    return {
        "current_price": current_price,
        "previous_price": previous_price,
        "change_pct": round(change_pct * 100, 4) if change_pct is not None else None,
        "significant": significant,
    }


async def _fetch_btc_price() -> float | None:
    """Call the configured BTC price API and return the GBP price."""
    url = settings.btc_price_api_url
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            # CoinGecko format: {"bitcoin": {"gbp": 12345.67}}
            price = (
                data.get("bitcoin", {}).get("gbp")
                or data.get("data", {}).get("priceUsd")
            )
            if price is None:
                logger.error("checker: unexpected BTC API response format — %s", data)
                return None
            return float(price)
    except httpx.HTTPError as exc:
        logger.error("checker: HTTP error fetching BTC price — %s", exc)
        return None
    except (ValueError, KeyError, TypeError) as exc:
        logger.error("checker: failed to parse BTC price response — %s", exc)
        return None


async def get_seasonality_multiplier(
    db: AsyncSession, account_id: uuid.UUID, month: int
) -> float:
    """Return the budget multiplier for a given account and calendar month.

    The multiplier is stored as a percentage modifier (e.g. 10.0 = +10%),
    converted to a float multiplier (e.g. 1.10). Defaults to 1.0 if not set.

    Args:
        db: Async database session.
        account_id: ATLAS account UUID.
        month: Calendar month as integer (1–12).

    Returns:
        Float multiplier (e.g. 1.1 for +10%, 0.9 for -10%).
    """
    result = await db.execute(
        select(SeasonalityConfig.budget_modifier_percent).where(
            SeasonalityConfig.account_id == account_id,
            SeasonalityConfig.month == month,
        )
    )
    modifier: float | None = result.scalar_one_or_none()

    if modifier is None:
        logger.debug(
            "checker: no seasonality config for account %s month %d — using 1.0",
            account_id, month,
        )
        return 1.0

    multiplier = 1.0 + (modifier / 100.0)
    logger.debug(
        "checker: seasonality multiplier for account %s month %d — %.4f",
        account_id, month, multiplier,
    )
    return round(multiplier, 4)


async def get_market_summary(
    db: AsyncSession, account_id: uuid.UUID
) -> dict[str, Any]:
    """Return a market summary for the given account.

    Includes:
    - Latest MarketCondition records from the last 30 days
    - Current month's seasonality multiplier
    - Most recent BTC price and crash flag

    Args:
        db: Async database session.
        account_id: ATLAS account UUID (used for seasonality lookup).

    Returns:
        Dict with recent_conditions, current_month_multiplier, and latest_btc fields.
    """
    cutoff = date.today() - timedelta(days=_MARKET_SUMMARY_DAYS)
    current_month = datetime.now(tz=timezone.utc).month

    conditions_result = await db.execute(
        select(MarketCondition)
        .where(MarketCondition.date >= cutoff)
        .order_by(MarketCondition.date.desc())
    )
    conditions = list(conditions_result.scalars().all())

    seasonality = await get_seasonality_multiplier(db, account_id, current_month)

    recent: list[dict[str, Any]] = [
        {
            "date": str(c.date),
            "btc_price": c.btc_price,
            "btc_7d_change_percent": c.btc_7d_change_percent,
            "is_btc_crash": c.is_btc_crash,
            "notes": c.notes,
        }
        for c in conditions
    ]

    latest = conditions[0] if conditions else None

    logger.info(
        "checker: market summary for account %s — %d conditions, multiplier=%.4f",
        account_id, len(recent), seasonality,
    )
    return {
        "recent_conditions": recent,
        "current_month": current_month,
        "current_month_multiplier": seasonality,
        "latest_btc_price": latest.btc_price if latest else None,
        "latest_btc_crash": latest.is_btc_crash if latest else False,
        "latest_date": str(latest.date) if latest else None,
    }
