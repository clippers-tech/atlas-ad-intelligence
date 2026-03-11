"""Apify Facebook Ads Scraper — fetches competitor ads via Apify actor.

Uses the apify/facebook-ads-scraper actor to pull ads from the
Meta Ad Library for a given Facebook Page ID.

GUARDRAILS:
- resultsLimit enforced on every run (default 10, max 50)
- Cost estimate returned with every start
- Settings controlled via APIFY_DEFAULT_ADS / APIFY_MAX_ADS_PER_FETCH

Pricing: ~$5 per 1000 results ($0.005/ad).
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_APIFY_BASE = "https://api.apify.com/v2"
_ACTOR_ID = "apify~facebook-ads-scraper"
_TIMEOUT = 30.0


class ApifyScraperError(Exception):
    """Raised when the Apify scraper fails."""
    pass


def _clamp_limit(requested: int) -> int:
    """Enforce hard ceiling on results. Never exceed config max."""
    hard_max = settings.apify_max_ads_per_fetch
    clamped = max(1, min(requested, hard_max))
    if requested > hard_max:
        logger.warning(
            "apify: requested %d ads, clamped to hard max %d",
            requested, hard_max,
        )
    return clamped


def estimate_cost(num_ads: int) -> float:
    """Estimate Apify cost for a given number of ads."""
    return round(num_ads * settings.apify_cost_per_ad, 4)


def _build_ad_library_url(page_id: str, country: str = "ALL") -> str:
    """Build a Meta Ad Library URL for a specific page."""
    return (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=active&ad_type=all"
        f"&country={country}"
        f"&view_all_page_id={page_id}"
    )


async def start_run(
    page_id: str,
    country: str = "ALL",
    max_ads: int | None = None,
) -> dict[str, Any]:
    """Start an Apify scraper run. Returns run_id, dataset_id, cost.

    max_ads is clamped to APIFY_MAX_ADS_PER_FETCH (default 50).
    If not provided, uses APIFY_DEFAULT_ADS (default 10).
    """
    token = settings.apify_api_token
    if not token:
        raise ApifyScraperError("APIFY_API_TOKEN not configured")

    limit = _clamp_limit(max_ads or settings.apify_default_ads)
    ad_library_url = _build_ad_library_url(page_id, country)

    # Correct Apify actor input format
    run_input = {
        "startUrls": [{"url": ad_library_url}],
        "resultsLimit": limit,
        "isDetailsPerAd": False,
        "includeAboutPage": False,
        "onlyTotal": False,
    }

    cost_est = estimate_cost(limit)
    logger.info(
        "apify: starting run page_id=%s limit=%d est_cost=$%.4f",
        page_id, limit, cost_est,
    )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(
            f"{_APIFY_BASE}/acts/{_ACTOR_ID}/runs?token={token}",
            json=run_input,
        )
        data = resp.json().get("data", resp.json())

        run_id = data.get("id", "")
        dataset_id = data.get("defaultDatasetId", "")
        status = data.get("status", "UNKNOWN")

        if not run_id:
            error = resp.json().get("error", {})
            raise ApifyScraperError(
                f"Failed to start: {error.get('message', 'Unknown')}"
            )

        logger.info(
            "apify: run started id=%s dataset=%s status=%s",
            run_id, dataset_id, status,
        )
        return {
            "run_id": run_id,
            "dataset_id": dataset_id,
            "status": status,
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
    fetch_limit = _clamp_limit(
        limit or settings.apify_default_ads
    )

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{_APIFY_BASE}/datasets/{dataset_id}/items"
            f"?token={token}&limit={fetch_limit}",
        )
        raw_ads = resp.json()

    if not isinstance(raw_ads, list):
        raise ApifyScraperError(
            f"Unexpected response: {type(raw_ads)}"
        )

    parsed = [_parse_apify_ad(ad) for ad in raw_ads]
    logger.info(
        "apify: parsed %d ads from dataset %s", len(parsed), dataset_id
    )
    return parsed


def _parse_apify_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert Apify ad record into our ingest format."""
    snapshot = raw.get("snapshot", {})
    cards = snapshot.get("cards", [])
    first_card = cards[0] if cards else {}

    # Extract ad text
    ad_text = first_card.get("body")
    if not ad_text:
        body = snapshot.get("body")
        if isinstance(body, dict):
            markup = body.get("markup", {})
            if isinstance(markup, dict):
                ad_text = markup.get("__html")
        elif isinstance(body, str):
            ad_text = body

    hook_text = first_card.get("title") or snapshot.get("title")
    cta_type = snapshot.get("ctaText") or first_card.get("ctaText")

    creative_url = (
        first_card.get("resizedImageUrl")
        or first_card.get("originalImageUrl")
        or first_card.get("videoPreviewImageUrl")
    )
    if not creative_url:
        images = snapshot.get("images", [])
        if images and isinstance(images[0], dict):
            creative_url = images[0].get("resizedImageUrl")

    offer_text = first_card.get("linkDescription")

    platforms = raw.get("publisherPlatform", [])
    platform_str = ", ".join(platforms) if platforms else None

    return {
        "creative_url": creative_url,
        "ad_text": ad_text,
        "hook_text": hook_text,
        "offer_text": offer_text,
        "cta_type": cta_type,
        "estimated_spend_range": None,
        "impression_range": None,
        "hook_type": platform_str,
    }
