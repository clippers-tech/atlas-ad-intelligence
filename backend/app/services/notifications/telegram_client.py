"""Telegram notification client — sends messages via Bot API."""

import asyncio
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.telegram.org"
_SEND_TIMEOUT = 10.0
_RATE_LIMIT_SLEEP = 1.5  # Telegram allows ~30 msg/sec per bot, 1 msg/sec per chat


class TelegramClient:
    """Async HTTP client for Telegram Bot API.

    Sends messages to specified chat IDs using the bot token from settings.
    """

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    @property
    def _bot_token(self) -> str:
        return settings.telegram_bot_token

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=_BASE_URL,
                timeout=_SEND_TIMEOUT,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
    ) -> bool:
        """Send a message to a Telegram chat.

        Args:
            chat_id: Telegram chat or group ID (as string).
            text: Message text. HTML tags are supported when parse_mode='HTML'.
            parse_mode: 'HTML' (default) or 'Markdown'.
            disable_web_page_preview: Suppress URL link previews.

        Returns:
            True on success, False on failure (error is logged).
        """
        if not self._bot_token:
            logger.error("telegram_client: no bot token configured — cannot send message")
            return False

        payload = {
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram max message length
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        url = f"/bot{self._bot_token}/sendMessage"
        try:
            client = await self._get_client()
            response = await client.post(url, json=payload)

            if response.status_code == 429:
                retry_after = int(response.json().get("parameters", {}).get("retry_after", 5))
                logger.warning("telegram_client: rate limited, sleeping %ds", retry_after)
                await asyncio.sleep(retry_after)
                response = await client.post(url, json=payload)

            response.raise_for_status()
            logger.debug("telegram_client: message sent to chat %s", chat_id)
            await asyncio.sleep(_RATE_LIMIT_SLEEP)
            return True

        except httpx.HTTPStatusError as exc:
            logger.error(
                "telegram_client: HTTP error sending to chat %s — %s",
                chat_id, exc.response.text,
            )
            return False
        except Exception as exc:
            logger.error("telegram_client: unexpected error sending to chat %s — %s", chat_id, exc)
            return False


# Module-level singleton
telegram_client = TelegramClient()
