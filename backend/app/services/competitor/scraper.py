"""Competitor scraper — fetches competitor ads via Apify Facebook Ad Library."""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.competitor_ad import CompetitorAd
from app.models.competitor_config import CompetitorConfig

logger = logging.getLogger(__name__)

_APIFY_RUN_URL = "https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs"
_APIFY_RUN_TIMEOUT = 120.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _run_apify_scraper(page_id: str) -> list[dict]:
    """Trigger an Apify Facebook Ads Scraper run and return raw ad items."""
    if not settings.apify_api_token:
        logger.warning("scraper: apify_api_token not configured")
        return []

    payload = {"pageIds": [page_id], "resultsLimit": 100, "adActiveStatus": "ALL"}
    params = {"token": settings.apify_api_token, "waitForFinish": 120}

    try:
        async with httpx.AsyncClient(timeout=_APIFY_RUN_TIMEOUT) as client:
            resp = await client.post(_APIFY_RUN_URL, json=payload, params=params)
            resp.raise_for_status()
            run_data = resp.json()

        dataset_id = run_data.get("data", {}).get("defaultDatasetId") or run_data.get(
            "defaultDatasetId"
        )
        if not dataset_id:
            logger.warning("scraper: no dataset_id in Apify response for page %s", page_id)
            return []

        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
        async with httpx.AsyncClient(timeout=30.0) as client:
            items_resp = await client.get(
                items_url, params={"token": settings.apify_api_token, "format": "json"}
            )
            items_resp.raise_for_status()
            return items_resp.json() or []

    except httpx.HTTPStatusError as exc:
        logger.error("scraper: Apify HTTP %d for page %s", exc.response.status_code, page_id)
        return []
    except Exception as exc:
        logger.exception("scraper: error scraping page %s — %s", page_id, exc)
        return []


def _parse_ad_fields(raw: dict) -> dict:
    """Map Apify response keys to CompetitorAd column names."""
    return {
        "creative_url": raw.get("snapshotUrl") or raw.get("creative_url"),
        "ad_text": raw.get("bodyText") or raw.get("ad_text"),
        "hook_text": raw.get("title") or raw.get("hook_text"),
        "estimated_spend_range": raw.get("spendRange") or raw.get("estimated_spend_range"),
        "impression_range": raw.get("impressionRange") or raw.get("impression_range"),
        "cta_type": raw.get("callToAction") or raw.get("cta_type"),
        "offer_text": raw.get("linkDescription") or raw.get("offer_text"),
    }


async def scrape_competitors(db: AsyncSession, account_id: UUID) -> dict:
    """Scrape competitor ads for all active CompetitorConfigs on an account.

    Upserts CompetitorAd records keyed on creative_url — updates last_seen
    for existing ads, inserts new ones. All records are scoped to account_id.

    Returns:
        Dict with keys: competitors_scraped, new_ads_found, total_ads.
    """
    logger.info("scraper: starting — account_id=%s", account_id)

    configs = list(
        (
            await db.execute(
                select(CompetitorConfig).where(
                    and_(
                        CompetitorConfig.account_id == account_id,
                        CompetitorConfig.is_active == True,  # noqa: E712
                    )
                )
            )
        ).scalars().all()
    )

    if not configs:
        logger.info("scraper: no active configs for account %s", account_id)
        return {"competitors_scraped": 0, "new_ads_found": 0, "total_ads": 0}

    now = _utcnow()
    scraped = new_found = total = 0

    for config in configs:
        if not config.meta_page_id:
            continue

        raw_ads = await _run_apify_scraper(config.meta_page_id)
        scraped += 1

        for raw in raw_ads:
            fields = _parse_ad_fields(raw)
            creative_url = fields.get("creative_url")
            existing = None

            if creative_url:
                res = await db.execute(
                    select(CompetitorAd).where(
                        and_(
                            CompetitorAd.account_id == account_id,
                            CompetitorAd.competitor_config_id == config.id,
                            CompetitorAd.creative_url == creative_url,
                        )
                    ).limit(1)
                )
                existing = res.scalar_one_or_none()

            if existing:
                existing.last_seen = now
                existing.is_active = True
            else:
                db.add(
                    CompetitorAd(
                        account_id=account_id,
                        competitor_config_id=config.id,
                        first_seen=now,
                        last_seen=now,
                        is_active=True,
                        **fields,
                    )
                )
                new_found += 1

            total += 1

        await db.commit()
        logger.info("scraper: '%s' — %d ads, %d new", config.competitor_name, len(raw_ads), new_found)

    logger.info("scraper: done — scraped=%d new=%d total=%d", scraped, new_found, total)
    return {"competitors_scraped": scraped, "new_ads_found": new_found, "total_ads": total}


async def detect_new_ads(
    db: AsyncSession, account_id: UUID, since_hours: int = 24
) -> list[dict]:
    """Return competitor ads first seen within the last N hours for an account.

    Args:
        db: Async database session.
        account_id: ATLAS account UUID — filters all results to this account.
        since_hours: Look-back window in hours (default 24).
    """
    since = _utcnow() - timedelta(hours=since_hours)
    result = await db.execute(
        select(CompetitorAd)
        .where(and_(CompetitorAd.account_id == account_id, CompetitorAd.first_seen >= since))
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
            "first_seen": ad.first_seen.isoformat() if ad.first_seen else None,
        }
        for ad in result.scalars().all()
    ]


async def get_competitor_summary(db: AsyncSession, account_id: UUID) -> list[dict]:
    """Return per-competitor ad counts and date ranges, scoped to account_id."""
    configs = list(
        (
            await db.execute(
                select(CompetitorConfig).where(CompetitorConfig.account_id == account_id)
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
                    func.min(CompetitorAd.first_seen).label("first_seen"),
                    func.max(CompetitorAd.last_seen).label("last_seen"),
                ).where(scope)
            )
        ).one()
        active_count = (
            await db.execute(
                select(func.count(CompetitorAd.id)).where(
                    and_(scope, CompetitorAd.is_active == True)  # noqa: E712
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
                "first_seen": totals_row.first_seen.isoformat() if totals_row.first_seen else None,
                "last_seen": totals_row.last_seen.isoformat() if totals_row.last_seen else None,
            }
        )

    return summaries
