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

    # Meta Marketing API
    meta_app_id: str = ""
    meta_app_secret: str = ""
    meta_system_user_token: str = ""
    meta_ad_account_ids: str = ""  # Comma-separated
    meta_ad_library_token: str = ""  # For Ad Library API



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
