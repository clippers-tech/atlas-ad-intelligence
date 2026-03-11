"""CompetitorConfig — which competitors to watch per account.

Stores both identity info (name, page ID, website) and Apify scraper
config (facebook_url, country, media_type, platforms, language) so each
competitor can have tailored scrape settings.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class CompetitorConfig(Base):
    __tablename__ = "competitor_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id"),
        nullable=False, index=True,
    )
    competitor_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    meta_page_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    website_url: Mapped[str | None] = mapped_column(
        String(2000), nullable=True
    )

    # Apify scraper config
    facebook_url: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Facebook page URL e.g. https://www.facebook.com/SHEINOFFICIAL",
    )
    scraper_country: Mapped[str] = mapped_column(
        String(10), default="ALL", server_default="ALL",
        comment="Country filter: ALL, US, GB, AU, etc.",
    )
    scraper_media_type: Mapped[str] = mapped_column(
        String(20), default="all", server_default="all",
        comment="Media filter: all, image, video, meme",
    )
    scraper_platforms: Mapped[str] = mapped_column(
        String(100), default="facebook,instagram",
        server_default="facebook,instagram",
        comment="Comma-separated: facebook, instagram, messenger, audience_network",
    )
    scraper_language: Mapped[str] = mapped_column(
        String(10), default="en", server_default="en",
        comment="Content language code: en, es, fr, etc.",
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(),
    )

    ads = relationship(
        "CompetitorAd", back_populates="config", lazy="selectin"
    )
