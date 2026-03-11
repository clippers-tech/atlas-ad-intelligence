"""Apify Facebook Ads Scraper — fetches competitor ads via Apify actor.

Supports two startUrl types per the actor docs:
1. Facebook page URL: https://www.facebook.com/SHEINOFFICIAL
2. Ad Library filtered URL with country, language, media, platforms

GUARDRAILS:
- resultsLimit enforced on every run (default 10, max 50)
- Cost estimate returned with every start
- Settings via APIFY_DEFAULT_ADS / APIFY_MAX_ADS_PER_FETCH

Pricing: ~$5 per 1000 results ($0.005/ad).
"""

import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.config import settings
from app.services.competitor.apify_parser import parse_apify_ad

logger = logging.getLogger(__name__)

_APIFY_BASE = "https://api.apify.com/v2"
_ACTOR_ID = "apify~facebook-ads-scraper"
_TIMEOUT = 30.0


class ApifyScraperError(Exception):
    """Raised when the Apify scraper fails."""
    pass


def _clamp_limit(requested: int) -> int:
    """Enforce hard ceiling on results."""
    hard_max = settings.apify_max_ads_per_fetch
    clamped = max(1, min(requested, hard_max))
    if requested > hard_max:
        logger.warning(
            "apify: requested %d ads, clamped to %d", requested, hard_max
        )
    return clamped


def estimate_cost(num_ads: int) -> float:
    """Estimate Apify cost for a given number of ads."""
    return round(num_ads * settings.apify_cost_per_ad, 4)


def build_start_urls(
    page_id: str | None = None,
    facebook_url: str | None = None,
    country: str = "ALL",
    media_type: str = "all",
    platforms: str = "facebook,instagram",
    language: str = "en",
) -> list[dict[str, str]]:
    """Build startUrls array for the Apify actor.

    Two URL types supported:
    1. Page URL: https://www.facebook.com/SHEINOFFICIAL
    2. Ad Library URL with full filter params
    """
    urls: list[dict[str, str]] = []

    # Add page URL if we have facebook_url
    if facebook_url and facebook_url.strip():
        urls.append({"url": facebook_url.strip()})

    # Build Ad Library filtered URL if we have page_id
    if page_id:
        parts = [
            "https://www.facebook.com/ads/library/",
            "?active_status=active",
            "&ad_type=all",
            f"&content_languages[0]={quote(language)}",
            f"&country={quote(country)}",
            "&is_targeted_country=false",
        ]
        if media_type and media_type != "all":
            parts.append(f"&media_type={quote(media_type)}")
        platform_list = [
            p.strip() for p in platforms.split(",") if p.strip()
        ]
        for i, plat in enumerate(platform_list):
            parts.append(f"&publisher_platforms[{i}]={quote(plat)}")
        parts.append("&search_type=page")
        parts.append(f"&view_all_page_id={page_id}")
        urls.append({"url": "".join(parts)})

    if not urls:
        raise ApifyScraperError(
            "No Facebook URL or Page ID — cannot build scraper URLs"
        )
    return urls


async def start_run(
    page_id: str | None = None,
    facebook_url: str | None = None,
    country: str = "ALL",
    media_type: str = "all",
    platforms: str = "facebook,instagram",
    language: str = "en",
    max_ads: int | None = None,
) -> dict[str, Any]:
    """Start an Apify scraper run with full config."""
    token = settings.apify_api_token
    if not token:
        raise ApifyScraperError("APIFY_API_TOKEN not configured")

    limit = _clamp_limit(max_ads or settings.apify_default_ads)
    start_urls = build_start_urls(
        page_id=page_id, facebook_url=facebook_url,
        country=country, media_type=media_type,
        platforms=platforms, language=language,
    )

    run_input = {
        "startUrls": start_urls,
        "resultsLimit": limit,
        "isDetailsPerAd": False,
        "includeAboutPage": False,
        "onlyTotal": False,
    }

    cost_est = estimate_cost(limit)
    logger.info(
        "apify: starting run page_id=%s urls=%d limit=%d cost=$%.4f",
        page_id, len(start_urls), limit, cost_est,
    )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_APIFY_BASE}/acts/{_ACTOR_ID}/runs?token={token}",
            json=run_input,
        )
        data = resp.json().get("data", resp.json())
        run_id = data.get("id", "")
        dataset_id = data.get("defaultDatasetId", "")
        run_status = data.get("status", "UNKNOWN")

        if not run_id:
            error = resp.json().get("error", {})
            raise ApifyScraperError(
                f"Failed to start: {error.get('message', 'Unknown')}"
            )

        return {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "status": run_status,
            "results_limit": limit,
            "estimated_cost": cost_est,
        }


async def check_run_status(run_id: str) -> dict[str, Any]:
    """Check the status of an Apify run."""
    token = settings.apify_api_token
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{_APIFY_BASE}/actor-runs/{run_id}?token={token}"
        )
        data = resp.json().get("data", {})
        return {
            "run_id": run_id,
            "status": data.get("status", "UNKNOWN"),
            "dataset_id": data.get("defaultDatasetId", ""),
        }


async def get_run_results(
    dataset_id: str, limit: int | None = None
) -> list[dict[str, Any]]:
    """Fetch parsed results from a completed Apify run."""
    token = settings.apify_api_token
    fetch_limit = _clamp_limit(limit or settings.apify_default_ads)

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{_APIFY_BASE}/datasets/{dataset_id}/items"
            f"?token={token}&limit={fetch_limit}",
        )
        raw_ads = resp.json()

    if not isinstance(raw_ads, list):
        raise ApifyScraperError(f"Unexpected response: {type(raw_ads)}")

    parsed = [parse_apify_ad(ad) for ad in raw_ads]
    logger.info(
        "apify: parsed %d ads from dataset %s", len(parsed), dataset_id
    )
    return parsed
