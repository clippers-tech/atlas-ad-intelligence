"""Competitor data service — stores and queries competitor ad data.

Scraping is handled by Perplexity Computer via scheduled runs.
Computer calls POST /api/competitors/ads to ingest discovered ads.
This module provides the DB queries and summary logic.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.competitor_ad import CompetitorAd
from app.models.competitor_config import CompetitorConfig

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def ingest_competitor_ads(
    db: AsyncSession,
    account_id: UUID,
    competitor_config_id: UUID,
    ads_data: list[dict],
) -> dict:
    """Ingest competitor ads from an external source (Perplexity Computer).

    Upserts CompetitorAd records keyed on creative_url — updates last_seen
    for existing ads, inserts new ones. All records scoped to account_id.

    Returns:
        Dict with keys: new_ads_found, updated, total.
    """
    now = _utcnow()
    new_found = updated = 0

    for raw in ads_data:
        creative_url = raw.get("creative_url")
        existing = None

        if creative_url:
            res = await db.execute(
                select(CompetitorAd).where(
                    and_(
                        CompetitorAd.account_id == account_id,
                        CompetitorAd.competitor_config_id == competitor_config_id,
                        CompetitorAd.creative_url == creative_url,
                    )
                ).limit(1)
            )
            existing = res.scalar_one_or_none()

        if existing:
            existing.last_seen = now
            existing.is_active = True
            updated += 1
        else:
            db.add(
                CompetitorAd(
                    account_id=account_id,
                    competitor_config_id=competitor_config_id,
                    first_seen=now,
                    last_seen=now,
                    is_active=True,
                    creative_url=creative_url,
                    ad_text=raw.get("ad_text"),
                    hook_text=raw.get("hook_text"),
                    estimated_spend_range=raw.get("estimated_spend_range"),
                    impression_range=raw.get("impression_range"),
                    cta_type=raw.get("cta_type"),
                    offer_text=raw.get("offer_text"),
                )
            )
            new_found += 1

    await db.commit()
    total = new_found + updated
    logger.info(
        "competitor_ingest: account=%s config=%s new=%d updated=%d",
        account_id, competitor_config_id, new_found, updated,
    )
    return {"new_ads_found": new_found, "updated": updated, "total": total}


async def detect_new_ads(
    db: AsyncSession, account_id: UUID, since_hours: int = 24
) -> list[dict]:
    """Return competitor ads first seen within the last N hours."""
    since = _utcnow() - timedelta(hours=since_hours)
    result = await db.execute(
        select(CompetitorAd)
        .where(
            and_(
                CompetitorAd.account_id == account_id,
                CompetitorAd.first_seen >= since,
            )
        )
        .order_by(CompetitorAd.first_seen.desc())
    )
    return [
        {
            "id": str(ad.id),
            "competitor_config_id": str(ad.competitor_config_id),
            "creative_url": ad.creative_url,
            "ad_text": ad.ad_text,
            "hook_text": ad.hook_text,
            "cta_type": ad.cta_type,
            "first_seen": (
                ad.first_seen.isoformat() if ad.first_seen else None
            ),
        }
        for ad in result.scalars().all()
    ]


async def get_competitor_summary(
    db: AsyncSession, account_id: UUID
) -> list[dict]:
    """Return per-competitor ad counts and date ranges."""
    configs = list(
        (
            await db.execute(
                select(CompetitorConfig).where(
                    CompetitorConfig.account_id == account_id
                )
            )
        ).scalars().all()
    )

    summaries: list[dict] = []
    for config in configs:
        scope = and_(
            CompetitorAd.account_id == account_id,
            CompetitorAd.competitor_config_id == config.id,
        )
        totals_row = (
            await db.execute(
                select(
                    func.count(CompetitorAd.id).label("total"),
                    func.min(CompetitorAd.first_seen).label("first"),
                    func.max(CompetitorAd.last_seen).label("last"),
                ).where(scope)
            )
        ).one()
        active_count = (
            await db.execute(
                select(func.count(CompetitorAd.id)).where(
                    and_(scope, CompetitorAd.is_active == True)
                )
            )
        ).scalar_one_or_none() or 0

        summaries.append(
            {
                "competitor_config_id": str(config.id),
                "competitor_name": config.competitor_name,
                "meta_page_id": config.meta_page_id,
                "is_active": config.is_active,
                "total_ads": totals_row.total or 0,
                "active_ads": active_count,
                "first_seen": (
                    totals_row.first.isoformat()
                    if totals_row.first else None
                ),
                "last_seen": (
                    totals_row.last.isoformat()
                    if totals_row.last else None
                ),
            }
        )

    return summaries
