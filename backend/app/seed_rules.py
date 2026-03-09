"""Default automation rules for each ATLAS account.

Called by app.seed — not a standalone entry point.
"""

import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule


# ---------------------------------------------------------------------------
# Rule definitions
# Each entry is a dict; target_cpa and target_cpl placeholders are resolved
# at call time using the account's actual values.
# ---------------------------------------------------------------------------

def _rules_for_account(account_id: uuid.UUID, target_cpa: float, target_cpl: float, target_roas: float) -> list[Rule]:
    """Return all 12 default Rule objects for the given account."""

    definitions = [
        # ── KILL RULES ──────────────────────────────────────────────────────
        {
            "name": "High Spend Zero Conversions",
            "description": "Pause ads that have spent over £50 with zero conversions.",
            "type": "kill",
            "condition_json": json.dumps({
                "metric": "spend", "operator": ">", "value": 50,
                "and": [{"metric": "conversions", "operator": "==", "value": 0}]
            }),
            "action_json": json.dumps({"action": "pause"}),
            "cooldown_minutes": 60,
            "priority": 10,
        },
        {
            "name": "CPA Over 2x Target",
            "description": f"Pause ads where CPA exceeds 2× the target (£{target_cpa * 2:.0f}).",
            "type": "kill",
            "condition_json": json.dumps({
                "metric": "cpa", "operator": ">", "value": round(target_cpa * 2, 2)
            }),
            "action_json": json.dumps({"action": "pause"}),
            "cooldown_minutes": 120,
            "priority": 9,
        },
        {
            "name": "CTR Below 0.5%",
            "description": "Pause low-CTR ads that have meaningful spend.",
            "type": "kill",
            "condition_json": json.dumps({
                "metric": "ctr", "operator": "<", "value": 0.5,
                "and": [{"metric": "spend", "operator": ">", "value": 30}]
            }),
            "action_json": json.dumps({"action": "pause"}),
            "cooldown_minutes": 120,
            "priority": 8,
        },
        {
            "name": "Frequency Over 3.5",
            "description": "Pause high-frequency ads to avoid audience fatigue.",
            "type": "kill",
            "condition_json": json.dumps({
                "metric": "frequency", "operator": ">", "value": 3.5
            }),
            "action_json": json.dumps({"action": "pause"}),
            "cooldown_minutes": 180,
            "priority": 7,
        },

        # ── SCALE RULES ─────────────────────────────────────────────────────
        {
            "name": "CPA Below Target Winner",
            "description": f"Scale ads beating the CPA target (£{target_cpa:.0f}) with 3+ conversions.",
            "type": "scale",
            "condition_json": json.dumps({
                "metric": "cpa", "operator": "<", "value": target_cpa,
                "and": [{"metric": "conversions", "operator": ">", "value": 3}]
            }),
            "action_json": json.dumps({"action": "increase_budget", "percent": 20}),
            "cooldown_minutes": 360,
            "priority": 6,
        },
        {
            "name": "ROAS Above Target",
            "description": f"Scale high-ROAS ads (>{target_roas}×) with meaningful spend.",
            "type": "scale",
            "condition_json": json.dumps({
                "metric": "roas", "operator": ">", "value": target_roas,
                "and": [{"metric": "spend", "operator": ">", "value": 100}]
            }),
            "action_json": json.dumps({"action": "increase_budget", "percent": 15}),
            "cooldown_minutes": 360,
            "priority": 5,
        },
        {
            "name": "CTR Above 2%",
            "description": f"Scale ads with strong CTR and CPL under target (£{target_cpl:.0f}).",
            "type": "scale",
            "condition_json": json.dumps({
                "metric": "ctr", "operator": ">", "value": 2.0,
                "and": [{"metric": "cpl", "operator": "<", "value": target_cpl}]
            }),
            "action_json": json.dumps({"action": "increase_budget", "percent": 10}),
            "cooldown_minutes": 360,
            "priority": 4,
        },

        # ── LAUNCH RULES ────────────────────────────────────────────────────
        {
            "name": "Duplicate Top Performer",
            "description": f"Duplicate ads with CPA below half the target (£{target_cpa * 0.5:.0f}) and 5+ conversions.",
            "type": "launch",
            "condition_json": json.dumps({
                "metric": "cpa", "operator": "<", "value": round(target_cpa * 0.5, 2),
                "and": [{"metric": "conversions", "operator": ">", "value": 5}]
            }),
            "action_json": json.dumps({"action": "duplicate"}),
            "cooldown_minutes": 1440,
            "priority": 3,
        },

        # ── BID / SCHEDULE RULES ────────────────────────────────────────────
        {
            "name": "Weekend Bid Down",
            "description": "Reduce budget on weekends (Sat/Sun) when conversion rates are typically lower.",
            "type": "bid",
            "condition_json": json.dumps({
                "metric": "day_of_week", "operator": "in", "value": [6, 7]
            }),
            "action_json": json.dumps({"action": "decrease_budget", "percent": 15}),
            "cooldown_minutes": 1440,
            "priority": 2,
        },
        {
            "name": "Weekday Morning Boost",
            "description": "Increase budget during peak weekday morning hours (08:00–12:00).",
            "type": "bid",
            "condition_json": json.dumps({
                "metric": "hour", "operator": "between", "value": [8, 12],
                "and": [{"metric": "day_of_week", "operator": "in", "value": [1, 2, 3, 4, 5]}]
            }),
            "action_json": json.dumps({"action": "increase_budget", "percent": 10}),
            "cooldown_minutes": 720,
            "priority": 2,
        },
        {
            "name": "Late Night Reduce",
            "description": "Cut budget during late-night hours (23:00–05:00) when engagement is low.",
            "type": "bid",
            "condition_json": json.dumps({
                "metric": "hour", "operator": "between", "value": [23, 5]
            }),
            "action_json": json.dumps({"action": "decrease_budget", "percent": 20}),
            "cooldown_minutes": 720,
            "priority": 2,
        },
        {
            "name": "High CPM Market Defense",
            "description": "Reduce budget when CPM exceeds £30 to protect against expensive inventory.",
            "type": "bid",
            "condition_json": json.dumps({
                "metric": "cpm", "operator": ">", "value": 30
            }),
            "action_json": json.dumps({"action": "decrease_budget", "percent": 10}),
            "cooldown_minutes": 360,
            "priority": 1,
        },
    ]

    return [
        Rule(
            id=uuid.uuid4(),
            account_id=account_id,
            name=d["name"],
            description=d.get("description"),
            type=d["type"],
            condition_json=d["condition_json"],
            action_json=d["action_json"],
            is_enabled=True,
            priority=d["priority"],
            cooldown_minutes=d["cooldown_minutes"],
        )
        for d in definitions
    ]


async def seed_rules(session: AsyncSession, account_id: uuid.UUID, account_name: str,
                     target_cpa: float, target_cpl: float, target_roas: float) -> None:
    """Create 12 default rules for an account (no-op if they already exist)."""
    from sqlalchemy import select
    existing = await session.execute(
        select(Rule).where(Rule.account_id == account_id)
    )
    if existing.scalars().first() is not None:
        print(f"  [rules] Rules already exist for {account_name} — skipping.")
        return

    rules = _rules_for_account(account_id, target_cpa, target_cpl, target_roas)
    session.add_all(rules)
    await session.flush()
    print(f"  [rules] Created {len(rules)} rules for {account_name}.")
