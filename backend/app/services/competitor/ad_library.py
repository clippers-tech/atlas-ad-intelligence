"""Meta Ad Library API client — fetches competitor ads from public archive.

Uses the /ads_archive endpoint with search_page_ids to pull all active
ads for a given Facebook Page. Requires identity-verified token with
Ad Library API access.

Docs: https://developers.facebook.com/docs/graph-api/reference/ads_archive/
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = "https://graph.facebook.com/v21.0"
_TIMEOUT = 30.0

# Fields we request from the Ad Library API
_AD_FIELDS = ",".join([
    "id",
    "ad_creation_time",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_captions",
    "ad_creative_link_descriptions",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "page_id",
    "page_name",
    "publisher_platforms",
    "bylines",
    "languages",
])


class AdLibraryError(Exception):
    """Raised when the Ad Library API returns an error."""

    def __init__(self, message: str, code: int = 0, subcode: int = 0):
        super().__init__(message)
        self.code = code
        self.subcode = subcode


async def fetch_page_ads(
    page_id: str,
    country: str = "ALL",
    limit: int = 50,
    active_only: bool = True,
) -> list[dict[str, Any]]:
    """Fetch ads for a Facebook Page from the Ad Library.

    Args:
        page_id: The Facebook Page ID to search.
        country: ISO country code or 'ALL'.
        limit: Max ads per request page (max 50).
        active_only: If True, only fetch currently active ads.

    Returns:
        List of parsed ad dicts ready for ingest_competitor_ads().
    """
    token = settings.meta_ad_library_token
    if not token:
        raise AdLibraryError(
            "META_AD_LIBRARY_TOKEN not configured", code=0
        )

    params: dict[str, Any] = {
        "access_token": token,
        "search_page_ids": page_id,
        "ad_reached_countries": f"['{country}']",
        "ad_type": "ALL",
        "fields": _AD_FIELDS,
        "limit": min(limit, 50),
    }
    if active_only:
        params["ad_active_status"] = "ACTIVE"

    all_ads: list[dict[str, Any]] = []

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        url = f"{_BASE_URL}/ads_archive"
        page_count = 0

        while url and page_count < 10:  # cap at 10 pages (500 ads)
            page_count += 1
            logger.info(
                "ad_library: fetching page %d for page_id=%s",
                page_count, page_id,
            )

            resp = await client.get(url, params=params)
            data = resp.json()

            if "error" in data:
                err = data["error"]
                raise AdLibraryError(
                    err.get("message", "Unknown error"),
                    code=err.get("code", 0),
                    subcode=err.get("error_subcode", 0),
                )

            raw_ads = data.get("data", [])
            for raw in raw_ads:
                all_ads.append(_parse_ad(raw))

            # Follow pagination
            next_url = (
                data.get("paging", {}).get("next")
            )
            if next_url:
                url = next_url
                params = {}  # next URL has params baked in
            else:
                break

    logger.info(
        "ad_library: found %d ads for page_id=%s", len(all_ads), page_id
    )
    return all_ads


def _parse_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw Ad Library response into our ingest format."""
    bodies = raw.get("ad_creative_bodies", [])
    titles = raw.get("ad_creative_link_titles", [])
    descriptions = raw.get("ad_creative_link_descriptions", [])
    captions = raw.get("ad_creative_link_captions", [])

    ad_text = bodies[0] if bodies else None
    hook_text = titles[0] if titles else None
    offer_text = descriptions[0] if descriptions else None

    # Build the CTA from caption if available
    cta_type = captions[0] if captions else None

    return {
        "creative_url": raw.get("ad_snapshot_url"),
        "ad_text": ad_text,
        "hook_text": hook_text,
        "offer_text": offer_text,
        "cta_type": cta_type,
        "estimated_spend_range": None,
        "impression_range": None,
        "hook_type": None,
    }
