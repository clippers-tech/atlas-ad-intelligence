"""Meta Marketing API action functions — pause, resume, budget, duplicate, bid."""

import logging
from typing import Any

from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)


async def pause_ad(meta_ad_id: str) -> dict[str, Any]:
    """Pause a Meta ad by setting its status to PAUSED.

    Returns:
        Dict with key 'success' (bool) and optional 'error' message.
    """
    try:
        result = await meta_client.post(f"/{meta_ad_id}", {"status": "PAUSED"})
        logger.info("actions: paused ad %s", meta_ad_id)
        return {"success": bool(result.get("success")), "meta_ad_id": meta_ad_id}
    except Exception as exc:
        logger.error("actions: failed to pause ad %s — %s", meta_ad_id, exc)
        return {"success": False, "meta_ad_id": meta_ad_id, "error": str(exc)}


async def resume_ad(meta_ad_id: str) -> dict[str, Any]:
    """Resume (activate) a Meta ad by setting its status to ACTIVE.

    Returns:
        Dict with key 'success' (bool) and optional 'error' message.
    """
    try:
        result = await meta_client.post(f"/{meta_ad_id}", {"status": "ACTIVE"})
        logger.info("actions: resumed ad %s", meta_ad_id)
        return {"success": bool(result.get("success")), "meta_ad_id": meta_ad_id}
    except Exception as exc:
        logger.error("actions: failed to resume ad %s — %s", meta_ad_id, exc)
        return {"success": False, "meta_ad_id": meta_ad_id, "error": str(exc)}


async def update_budget(
    meta_adset_id: str, new_budget: float, budget_type: str = "daily_budget"
) -> dict[str, Any]:
    """Update daily or lifetime budget on a Meta ad set.

    Args:
        meta_adset_id: Meta ad set ID.
        new_budget: New budget in account currency (converted to cents for API).
        budget_type: 'daily_budget' (default) or 'lifetime_budget'.

    Returns:
        Dict with 'success' (bool) and optional 'error'.
    """
    budget_cents = int(new_budget * 100)
    try:
        result = await meta_client.post(
            f"/{meta_adset_id}", {budget_type: str(budget_cents)}
        )
        logger.info(
            "actions: updated %s for adset %s to %s (%d cents)",
            budget_type, meta_adset_id, new_budget, budget_cents,
        )
        return {"success": bool(result.get("success")), "meta_adset_id": meta_adset_id}
    except Exception as exc:
        logger.error("actions: failed to update budget for adset %s — %s", meta_adset_id, exc)
        return {"success": False, "meta_adset_id": meta_adset_id, "error": str(exc)}


async def duplicate_adset(meta_adset_id: str) -> dict[str, Any]:
    """Duplicate a Meta ad set using the copies endpoint.

    Returns:
        Dict with 'success' (bool), 'new_adset_id' if successful, or 'error'.
    """
    try:
        result = await meta_client.post(
            f"/{meta_adset_id}/copies",
            {"status_option": "PAUSED"},
        )
        new_id = result.get("copied_adset_id") or (result.get("copies") or [{}])[0].get("id")
        logger.info("actions: duplicated adset %s → new id %s", meta_adset_id, new_id)
        return {"success": True, "meta_adset_id": meta_adset_id, "new_adset_id": new_id}
    except Exception as exc:
        logger.error("actions: failed to duplicate adset %s — %s", meta_adset_id, exc)
        return {"success": False, "meta_adset_id": meta_adset_id, "error": str(exc)}


async def adjust_bid(meta_adset_id: str, new_bid: float) -> dict[str, Any]:
    """Adjust bid cap (bid_amount) for a Meta ad set.

    Args:
        meta_adset_id: Meta ad set ID.
        new_bid: New bid amount in account currency (converted to cents).

    Returns:
        Dict with 'success' (bool) and optional 'error'.
    """
    bid_cents = int(new_bid * 100)
    try:
        result = await meta_client.post(
            f"/{meta_adset_id}", {"bid_amount": str(bid_cents)}
        )
        logger.info(
            "actions: adjusted bid for adset %s to %s (%d cents)",
            meta_adset_id, new_bid, bid_cents,
        )
        return {"success": bool(result.get("success")), "meta_adset_id": meta_adset_id}
    except Exception as exc:
        logger.error("actions: failed to adjust bid for adset %s — %s", meta_adset_id, exc)
        return {"success": False, "meta_adset_id": meta_adset_id, "error": str(exc)}
