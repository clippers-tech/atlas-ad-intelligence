"""Parsers for Meta Insights API action & metric fields."""

import json
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


# Human-readable names for custom conversion IDs.
_CONV_NAMES: dict[str, str] = {
    "3284105835088992": "Clippers Ads - Booked Call",
    "3800918580212743": "Lumina – Booked Call Lead",
}

# All known custom conversion IDs per Meta ad-account.
# Used to build the tooltip breakdown (all conversions).
_ACCOUNT_CONV_IDS: dict[str, list[str]] = {
    "act_1103850885215983": [
        "3284105835088992",
        "3800918580212743",
    ],
}


def _conv_name(action_type: str) -> str:
    """Get human name for an action_type string."""
    if action_type == "lead":
        return "Lead (Form)"
    # offsite_conversion.custom.<id>
    parts = action_type.rsplit(".", 1)
    cid = parts[-1] if len(parts) > 1 else ""
    return _CONV_NAMES.get(cid, action_type)


def parse_results_and_breakdown(
    actions: list[dict] | None,
    meta_account_id: str,
    optimization_event: str | None,
) -> tuple[int, str | None]:
    """Count result + build conversion breakdown JSON.

    Returns (result_count, breakdown_json).
    result_count = only the optimization_event count.
    breakdown = ALL custom conversions found (for tooltip).
    """
    if not actions:
        return 0, None

    cc_ids = _ACCOUNT_CONV_IDS.get(meta_account_id, [])
    breakdown: list[dict[str, Any]] = []
    result = 0

    if cc_ids:
        # Build breakdown for all known custom conversions
        for cid in cc_ids:
            at = f"offsite_conversion.custom.{cid}"
            count = parse_actions(actions, at)
            if count > 0:
                breakdown.append({
                    "name": _conv_name(at),
                    "value": count,
                })
                if optimization_event and at == optimization_event:
                    result = count

        # If no optimization_event set, sum all
        if not optimization_event and breakdown:
            result = sum(b["value"] for b in breakdown)
    # Also check standard lead
    lead_count = parse_actions(actions, "lead")
    if lead_count > 0 and not cc_ids:
        breakdown.append({
            "name": "Lead (Form)", "value": lead_count,
        })
    # If no optimization_event matched, fallback
    if result == 0:
        if optimization_event:
            # Count the specific event directly
            result = parse_actions(
                actions, optimization_event,
            )
        elif not cc_ids:
            result = lead_count

    bd_json = json.dumps(breakdown) if breakdown else None
    return result, bd_json


def parse_result_cost(
    spend: float, results: int,
    cost_actions: list[dict] | None = None,
) -> float:
    """Cost per result: spend / results."""
    if results > 0:
        return round(spend / results, 2)
    if cost_actions:
        return parse_cost_per_action(
            cost_actions, "lead"
        )
    return 0.0
