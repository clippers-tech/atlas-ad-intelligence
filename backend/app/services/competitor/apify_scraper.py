"""Apify Facebook Ads Scraper — fetches competitor ads via Apify actor.

Uses the apify/facebook-ads-scraper actor to pull ads from the
Meta Ad Library for a given Facebook Page ID. No identity verification
needed — Apify handles the browsing.

Two-phase approach:
1. start_run() — kicks off the Apify actor, returns run_id
2. get_run_results() — checks if done, returns parsed ads

Pricing: ~$0.005 per ad.
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
    max_ads: int = 50,
) -> dict[str, str]:
    """Start an Apify scraper run. Returns run_id and dataset_id."""
    token = settings.apify_api_token
    if not token:
        raise ApifyScraperError("APIFY_API_TOKEN not configured")

    ad_library_url = _build_ad_library_url(page_id, country)
    run_input = {
        "startUrls": [{"url": ad_library_url}],
        "maxAds": max_ads,
        "scrapeAdDetails": False,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        logger.info(
            "apify: starting run for page_id=%s max_ads=%d",
            page_id, max_ads,
        )
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
    dataset_id: str, max_ads: int = 50
) -> list[dict[str, Any]]:
    """Fetch parsed results from a completed Apify run."""
    token = settings.apify_api_token
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.get(
            f"{_APIFY_BASE}/datasets/{dataset_id}/items"
            f"?token={token}&limit={max_ads}",
        )
        raw_ads = resp.json()

    if not isinstance(raw_ads, list):
        raise ApifyScraperError(
            f"Unexpected response: {type(raw_ads)}"
        )

    parsed = [_parse_apify_ad(ad) for ad in raw_ads]
    logger.info("apify: parsed %d ads from dataset %s", len(parsed), dataset_id)
    return parsed


async def fetch_page_ads(
    page_id: str,
    country: str = "ALL",
    max_ads: int = 50,
) -> list[dict[str, Any]]:
    """Convenience: start run, wait up to 5 min, return results.

    For production use, prefer start_run() + check_run_status() +
    get_run_results() for an async flow.
    """
    import asyncio

    run_info = await start_run(page_id, country, max_ads)
    run_id = run_info["run_id"]
    dataset_id = run_info["dataset_id"]

    # Poll for completion
    for _ in range(30):  # 30 * 10s = 5 min
        await asyncio.sleep(10)
        status_info = await check_run_status(run_id)
        status = status_info["status"]

        if status == "SUCCEEDED":
            return await get_run_results(dataset_id, max_ads)
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise ApifyScraperError(f"Run {run_id} ended: {status}")

    raise ApifyScraperError(f"Run {run_id} timed out after 5 min")


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

    # Hook from card title
    hook_text = first_card.get("title") or snapshot.get("title")

    # CTA
    cta_type = snapshot.get("ctaText") or first_card.get("ctaText")

    # Creative image URL
    creative_url = (
        first_card.get("resizedImageUrl")
        or first_card.get("originalImageUrl")
        or first_card.get("videoPreviewImageUrl")
    )
    if not creative_url:
        images = snapshot.get("images", [])
        if images and isinstance(images[0], dict):
            creative_url = images[0].get("resizedImageUrl")

    # Offer text from link description
    offer_text = first_card.get("linkDescription")

    # Platforms as comma-separated string
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
