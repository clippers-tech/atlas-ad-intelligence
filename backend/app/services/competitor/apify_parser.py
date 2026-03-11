"""Parse Apify facebook-ads-scraper output into our ingest format."""

from typing import Any


def parse_apify_ad(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert Apify ad record into our ingest format."""
    snapshot = raw.get("snapshot", {})
    cards = snapshot.get("cards", [])
    first_card = cards[0] if cards else {}

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
