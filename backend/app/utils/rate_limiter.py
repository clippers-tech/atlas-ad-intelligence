"""Meta API rate limiter — respects x-business-use-case-usage header.

Implements:
- Throttling when usage > 75% (2s sleep) or > 90% (300s sleep)
- Exponential backoff on error code 32 (rate limit hit)
- tenacity-based retry decorator for callers
"""

import asyncio
import functools
import json
import logging
from collections.abc import Callable
from typing import Any

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_HIGH_USAGE_THRESHOLD = 75
_CRITICAL_USAGE_THRESHOLD = 90
_HIGH_USAGE_SLEEP = 2
_CRITICAL_USAGE_SLEEP = 300
_MAX_BACKOFF = 60


class MetaRateLimitError(Exception):
    """Raised when Meta returns error code 32 (rate limited)."""


class RateLimiter:
    """Inspects Meta API response headers and throttles when needed."""

    async def check_response_headers(self, headers: dict[str, Any]) -> None:
        """Parse x-business-use-case-usage and sleep if thresholds exceeded."""
        raw = headers.get("x-business-use-case-usage") or headers.get(
            "X-Business-Use-Case-Usage"
        )
        if not raw:
            return

        try:
            usage_data: dict = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("rate_limiter: could not parse x-business-use-case-usage header")
            return

        max_usage = 0
        for _account_id, usages in usage_data.items():
            for entry in usages:
                pct = entry.get("call_count", 0)
                max_usage = max(max_usage, pct)

        if max_usage > _CRITICAL_USAGE_THRESHOLD:
            logger.warning(
                "rate_limiter: Meta API usage %d%% > 90%%, sleeping %ds",
                max_usage,
                _CRITICAL_USAGE_SLEEP,
            )
            await asyncio.sleep(_CRITICAL_USAGE_SLEEP)
        elif max_usage > _HIGH_USAGE_THRESHOLD:
            logger.info(
                "rate_limiter: Meta API usage %d%% > 75%%, sleeping %ds",
                max_usage,
                _HIGH_USAGE_SLEEP,
            )
            await asyncio.sleep(_HIGH_USAGE_SLEEP)

    async def handle_error_code(self, error_code: int) -> None:
        """If error code 32 (rate limit), raise MetaRateLimitError for retry."""
        if error_code == 32:
            logger.warning("rate_limiter: Meta error code 32 — raising for backoff")
            raise MetaRateLimitError("Meta API error code 32: rate limited")


def _make_retry_decorator() -> Callable:
    """Build a tenacity retry decorator for MetaRateLimitError."""
    return retry(
        retry=retry_if_exception_type(MetaRateLimitError),
        wait=wait_exponential(multiplier=1, min=1, max=_MAX_BACKOFF),
        stop=stop_after_attempt(6),  # 1, 2, 4, 8, 16, 32 → capped at 60
        reraise=True,
    )


# Module-level singleton and decorator
meta_rate_limiter = RateLimiter()

with_meta_rate_limit = _make_retry_decorator()
