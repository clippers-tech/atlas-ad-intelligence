"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """All environment variables for ATLAS."""

    # App
    app_env: str = "development"
    secret_key: str = "change-me"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://atlas:password@postgres:5432/atlas"

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Meta Marketing API
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_system_user_token: str = ""
    meta_ad_account_ids: str = ""  # Comma-separated

    # Calendly
    calendly_api_token: str = ""
    calendly_webhook_secret: str = ""

    # Stripe
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""

    # Claude (Anthropic)
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Apify
    apify_api_token: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_default_chat_id: str = ""

    # BTC Price
    btc_price_api_url: str = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=gbp"
    )

    @property
    def meta_account_ids_list(self) -> list[str]:
        """Parse comma-separated Meta ad account IDs."""
        if not self.meta_ad_account_ids:
            return []
        return [aid.strip() for aid in self.meta_ad_account_ids.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
