"""Rules engine — evaluates automation rules against ad metrics."""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_log import ActionLog
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.rule import Rule
from app.services.rules.dispatch import dispatch_action

logger = logging.getLogger(__name__)

_OPS: dict = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _eval_condition(
    value: float, operator: str, threshold: float
) -> bool:
    """Evaluate a single numeric condition."""
    fn = _OPS.get(operator)
    if fn is None:
        logger.warning("rules: unknown operator %r", operator)
        return False
    return fn(value, threshold)


def _metric_from_row(
    row: AdMetric, metric_name: str
) -> float | None:
    """Extract a named metric from an AdMetric row."""
    return getattr(row, metric_name, None)


def _eval_full_condition(
    metric_row: AdMetric, condition: dict
) -> bool:
    """Evaluate a condition tree including AND/OR branches.

    Shape: {"metric": "spend", "operator": ">", "value": 75,
            "and": [{"metric": "conversions", "operator": "==", "value": 0}]}
    """
    metric_name = condition.get("metric", "")
    operator = condition.get("operator", "")
    threshold = condition.get("value")

    if not metric_name or not operator or threshold is None:
        return False

    value = _metric_from_row(metric_row, metric_name)
    if value is None:
        return False

    if not _eval_condition(float(value), operator, float(threshold)):
        return False

    # AND — ALL must pass
    for sub in condition.get("and", []):
        if not _eval_full_condition(metric_row, sub):
            return False

    # OR — at least ONE must pass (if present)
    or_conditions = condition.get("or", [])
    if or_conditions:
        if not any(
            _eval_full_condition(metric_row, s)
            for s in or_conditions
        ):
            return False

    return True


def _build_snapshot(
    metric_row: AdMetric, condition: dict, ad_id
) -> dict:
    """Collect metric values referenced in a condition tree."""
    snap: dict = {"ad_id": str(ad_id)}
    name = condition.get("metric", "")
    if name:
        snap[name] = _metric_from_row(metric_row, name)
    for sub in condition.get("and", []):
        n = sub.get("metric", "")
        if n:
            snap[n] = _metric_from_row(metric_row, n)
    for sub in condition.get("or", []):
        n = sub.get("metric", "")
        if n:
            snap[n] = _metric_from_row(metric_row, n)
    return snap


async def check_cooldown(
    db: AsyncSession, rule_id: uuid.UUID, cooldown_minutes: int
) -> bool:
    """True if the rule fired recently (still in cooldown)."""
    cutoff = datetime.now(timezone.utc) - timedelta(
        minutes=cooldown_minutes
    )
    result = await db.execute(
        select(ActionLog.created_at)
        .where(
            ActionLog.rule_id == rule_id,
            ActionLog.created_at >= cutoff,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------

async def evaluate_rules_for_account(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict]:
    """Evaluate all enabled rules and execute actions."""
    horizon = datetime.now(timezone.utc) - timedelta(hours=1)

    rules_result = await db.execute(
        select(Rule).where(
            Rule.account_id == account_id,
            Rule.is_enabled.is_(True),
        ).order_by(Rule.priority.asc())
    )
    rules = list(rules_result.scalars().all())

    if not rules:
        logger.debug("rules: no active rules for %s", account_id)
        return []

    metrics_result = await db.execute(
        select(AdMetric)
        .where(
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= horizon,
        )
        .order_by(AdMetric.ad_id, AdMetric.timestamp.desc())
    )
    all_metrics = list(metrics_result.scalars().all())

    latest_by_ad: dict[uuid.UUID, AdMetric] = {}
    for m in all_metrics:
        if m.ad_id not in latest_by_ad:
            latest_by_ad[m.ad_id] = m

    actions_taken: list[dict] = []

    for rule in rules:
        try:
            condition = json.loads(rule.condition_json)
            action_cfg = json.loads(rule.action_json)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("rules: bad JSON in rule %s — %s", rule.id, exc)
            continue

        if await check_cooldown(db, rule.id, rule.cooldown_minutes):
            continue

        if (
            rule.budget_limit is not None
            and rule.budget_spent >= rule.budget_limit
        ):
            continue

        for ad_id, metric_row in latest_by_ad.items():
            if not _eval_full_condition(metric_row, condition):
                continue

            ad = await db.get(Ad, ad_id)
            if ad is None or ad.account_id != account_id:
                continue

            snapshot = _build_snapshot(metric_row, condition, ad_id)
            result = await dispatch_action(
                db, rule, ad, action_cfg, snapshot
            )
            if result:
                ad_spend = getattr(metric_row, "spend", 0.0) or 0.0
                rule.budget_spent = (rule.budget_spent or 0.0) + ad_spend
                await db.flush()
                actions_taken.append(result)
                break  # cooldown: one fire per rule per eval

    logger.info(
        "rules: account %s — %d action(s) from %d rule(s)",
        account_id, len(actions_taken), len(rules),
    )
    return actions_taken
