"""Parsers for Meta Insights API action & metric fields."""

from typing import Any


def _safe_int(val: Any) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _safe_float(val: Any) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def parse_actions(
    actions: list[dict] | None, key: str,
) -> int:
    """Extract a specific action count from Meta actions."""
    if not actions:
        return 0
    for a in actions:
        if a.get("action_type") == key:
            return int(a.get("value", 0))
    return 0


def parse_cost_per_action(
    cost_actions: list[dict] | None, key: str,
) -> float:
    if not cost_actions:
        return 0.0
    for a in cost_actions:
        if a.get("action_type") == key:
            return float(a.get("value", 0))
    return 0.0


def parse_outbound(row: dict) -> int:
    """outbound_clicks is an array of {action_type, value}."""
    oc = row.get("outbound_clicks")
    if not oc:
        return 0
    for item in oc:
        if item.get("action_type") == "outbound_click":
            return _safe_int(item.get("value", 0))
    return 0


def parse_website_ctr(row: dict) -> float:
    """website_ctr is an array of {action_type, value}."""
    wc = row.get("website_ctr")
    if not wc:
        return 0.0
    for item in wc:
        key = "offsite_conversion.fb_pixel_view_content"
        if item.get("action_type") == key:
            return _safe_float(item.get("value", 0))
    if wc:
        return _safe_float(wc[0].get("value", 0))
    return 0.0


# Custom conversion IDs that count as "results" per account.
# Maps Meta ad-account ID → list of custom conversion IDs.
_CUSTOM_CONV_IDS: dict[str, list[str]] = {
    # Lumina Clippers
    "act_1103850885215983": [
        "3284105835088992",   # Clippers Ads - Booked Call
        "3800918580212743",   # Lumina – Booked Call Lead
    ],
}


def parse_results(
    actions: list[dict] | None,
    meta_account_id: str,
) -> int:
    """Count results: custom conversions if configured,
    else fall back to standard 'lead' action."""
    if not actions:
        return 0
    cc_ids = _CUSTOM_CONV_IDS.get(meta_account_id, [])
    if cc_ids:
        total = 0
        for a in actions:
            at = a.get("action_type", "")
            for cid in cc_ids:
                if at == f"offsite_conversion.custom.{cid}":
                    total += int(a.get("value", 0))
        if total > 0:
            return total
    # Fallback: standard lead action
    return parse_actions(actions, "lead")


def parse_result_cost(
    cost_actions: list[dict] | None,
    meta_account_id: str,
    spend: float,
    results: int,
) -> float:
    """Cost per result: spend/results for custom conversions,
    else fall back to cost_per_action 'lead'."""
    if results > 0:
        return round(spend / results, 2)
    cc_ids = _CUSTOM_CONV_IDS.get(meta_account_id, [])
    if not cc_ids and cost_actions:
        return parse_cost_per_action(cost_actions, "lead")
    return 0.0
