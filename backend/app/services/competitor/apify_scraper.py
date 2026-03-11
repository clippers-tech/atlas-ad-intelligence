"""Apify Facebook Ads Scraper — fetches competitor ads via Apify actor.

Uses the apify/facebook-ads-scraper actor to pull ads from the
Meta Ad Library for a given Facebook Page ID. No identity verification
needed — Apify handles the browsing.

Pricing: ~$0.005 per ad.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_APIFY_BASE = "https://api.apify.com/v2"
_ACTOR_ID = "apify~facebook-ads-scraper"
_TIMEOUT = 300.0  # 5 min — scraper can take a while
_WAIT_SECS = 240  # Wait up to 4 min for run to finish


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


async def fetch_page_ads(
    page_id: str,
    country: str = "ALL",
    max_ads: int = 50,
) -> list[dict[str, Any]]:
    """Fetch ads for a Facebook Page via Apify scraper.

    Args:
        page_id: The Facebook Page ID to search.
        country: ISO country code or 'ALL'.
        max_ads: Maximum number of ads to fetch.

    Returns:
        List of parsed ad dicts ready for ingest_competitor_ads().
    """
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
        # Start the actor run and wait for it
        logger.info(
            "apify: starting run for page_id=%s max_ads=%d",
            page_id, max_ads,
        )
        resp = await client.post(
            f"{_APIFY_BASE}/acts/{_ACTOR_ID}/runs"
            f"?token={token}&waitForFinish={_WAIT_SECS}",
            json=run_input,
        )
        run_data = resp.json().get("data", resp.json())

        status = run_data.get("status", "UNKNOWN")
        dataset_id = run_data.get("defaultDatasetId")
        run_id = run_data.get("id", "?")

        if status not in ("SUCCEEDED", "RUNNING", "READY"):
            raise ApifyScraperError(
                f"Apify run {run_id} failed with status: {status}"
            )

        # If still running, poll until done
        if status in ("RUNNING", "READY"):
            dataset_id = await _poll_run(client, run_id, token)

        if not dataset_id:
            raise ApifyScraperError("No dataset returned from Apify run")

        # Fetch results from dataset
        items_resp = await client.get(
            f"{_APIFY_BASE}/datasets/{dataset_id}/items"
            f"?token={token}&limit={max_ads}",
        )
        raw_ads = items_resp.json()

    if not isinstance(raw_ads, list):
        raise ApifyScraperError(
            f"Unexpected Apify response: {type(raw_ads)}"
        )

    parsed = [_parse_apify_ad(ad) for ad in raw_ads]
    logger.info(
        "apify: fetched %d ads for page_id=%s (run=%s)",
        len(parsed), page_id, run_id,
    )
    return parsed


async def _poll_run(
    client: httpx.AsyncClient, run_id: str, token: str
) -> str:
    """Poll an Apify run until it finishes. Returns dataset ID."""
    import asyncio

    for _ in range(30):  # 30 * 10s = 5 min max
        await asyncio.sleep(10)
        resp = await client.get(
            f"{_APIFY_BASE}/actor-runs/{run_id}?token={token}"
        )
        data = resp.json().get("data", {})
        status = data.get("status", "UNKNOWN")
        logger.debug("apify: poll run=%s status=%s", run_id, status)

        if status == "SUCCEEDED":
            return data.get("defaultDatasetId", "")
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise ApifyScraperError(
                f"Apify run {run_id} ended with: {status}"
            )

    raise ApifyScraperError(f"Apify run {run_id} timed out after 5 min")


def _parse_apify_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert Apify ad record into our ingest format."""
    snapshot = raw.get("snapshot", {})
    cards = snapshot.get("cards", [])
    first_card = cards[0] if cards else {}

    # Extract ad text from card body or snapshot body
    ad_text = first_card.get("body")
    if not ad_text:
        body = snapshot.get("body")
        if isinstance(body, dict):
            markup = body.get("markup", {})
            ad_text = markup.get("__html") if isinstance(markup, dict) else None
        elif isinstance(body, str):
            ad_text = body

    # Extract hook from card title
    hook_text = first_card.get("title") or snapshot.get("title")

    # CTA
    cta_type = snapshot.get("ctaText") or first_card.get("ctaText")

    # Creative image URL — prefer first card image
    creative_url = (
        first_card.get("resizedImageUrl")
        or first_card.get("originalImageUrl")
        or first_card.get("videoPreviewImageUrl")
    )
    # If no card image, check snapshot images/videos
    if not creative_url:
        images = snapshot.get("images", [])
        if images and isinstance(images[0], dict):
            creative_url = images[0].get("resizedImageUrl")

    # Offer text from link description
    offer_text = first_card.get("linkDescription")

    # Platforms
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
        "hook_type": platform_str,  # Reuse hook_type for platforms
    }
