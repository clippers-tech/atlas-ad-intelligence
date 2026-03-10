"""Meta Marketing API HTTP client.

Wraps httpx.AsyncClient with:
- Circuit breaker protection
- Rate limit header inspection
- Cursor-based pagination
- Structured logging for every request
"""

import logging
from typing import Any, AsyncIterator

import httpx

from app.config import settings
from app.utils.circuit_breaker import meta_circuit
from app.utils.rate_limiter import MetaRateLimitError, meta_rate_limiter

logger = logging.getLogger(__name__)

_BASE_URL = "https://graph.facebook.com/v21.0"
_DEFAULT_TIMEOUT = 30.0


class MetaAPIClient:
    """Async HTTP client for Meta Graph API calls."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=_BASE_URL,
                timeout=_DEFAULT_TIMEOUT,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _auth_params(self) -> dict[str, str]:
        return {"access_token": settings.meta_system_user_token}

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform a GET request through circuit breaker + rate limiter."""
        merged = {**(params or {}), **self._auth_params()}

        async def _do_get() -> dict[str, Any]:
            client = await self._get_client()
            logger.debug("meta_client: GET %s params=%s", endpoint, list(merged.keys()))
            response = await client.get(endpoint, params=merged)
            response.raise_for_status()
            await meta_rate_limiter.check_response_headers(dict(response.headers))
            data = response.json()
            if "error" in data:
                err = data["error"]
                code = err.get("code", 0)
                await meta_rate_limiter.handle_error_code(code)
                raise httpx.HTTPStatusError(
                    f"Meta API error {code}: {err.get('message')}",
                    request=response.request,
                    response=response,
                )
            return data

        return await meta_circuit.call(_do_get)

    async def post(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Perform a POST request through circuit breaker + rate limiter."""
        payload = {**(data or {}), **self._auth_params()}

        async def _do_post() -> dict[str, Any]:
            client = await self._get_client()
            logger.debug("meta_client: POST %s keys=%s", endpoint, list(payload.keys()))
            response = await client.post(endpoint, data=payload)
            response.raise_for_status()
            await meta_rate_limiter.check_response_headers(dict(response.headers))
            result = response.json()
            if "error" in result:
                err = result["error"]
                code = err.get("code", 0)
                await meta_rate_limiter.handle_error_code(code)
                raise httpx.HTTPStatusError(
                    f"Meta API error {code}: {err.get('message')}",
                    request=response.request,
                    response=response,
                )
            return result

        return await meta_circuit.call(_do_post)

    async def paginate(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield each page of results following Meta cursor-based pagination."""
        current_params = dict(params or {})
        while True:
            page = await self.get(endpoint, current_params)
            yield page

            paging = page.get("paging", {})
            next_cursor = paging.get("cursors", {}).get("after")
            if not next_cursor or not paging.get("next"):
                break
            current_params["after"] = next_cursor
            logger.debug("meta_client: paginating → cursor %s", next_cursor[:20])


# Module-level singleton
meta_client = MetaAPIClient()
