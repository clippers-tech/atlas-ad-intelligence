"""MetaAuth — system user token management for Meta Marketing API."""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class MetaAuth:
    """Manages authentication headers for Meta Marketing API calls.

    System user tokens are long-lived (60+ days) and are not auto-refreshed.
    Refresh is a manual process via Meta Business Manager.
    """

    def __init__(self) -> None:
        self._token: str = settings.meta_system_user_token

    @property
    def token(self) -> str:
        return self._token

    def get_headers(self) -> dict[str, str]:
        """Return HTTP headers for Meta API requests."""
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def get_params(self) -> dict[str, str]:
        """Return query params that include the access token."""
        return {"access_token": self._token}

    async def refresh_token(self) -> None:
        """Placeholder — system user tokens are long-lived.

        Meta system user tokens do not support programmatic refresh.
        To refresh: log into Meta Business Manager → System Users → Generate token.
        This method exists for interface compatibility.
        """
        logger.info(
            "meta_auth.refresh_token called — system user tokens are long-lived, "
            "no action taken. Renew manually in Meta Business Manager."
        )

    def is_token_set(self) -> bool:
        """Return True if a token has been configured."""
        return bool(self._token)


# Module-level singleton
meta_auth = MetaAuth()
