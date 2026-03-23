"""Rules engine — evaluates automation rules against ad metrics.

Aggregates daily metric rows over a 7-day window, then evaluates
rule conditions against the per-ad totals.  Only ACTIVE ads are
checked (no point killing already-paused ads).
"""

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
from app.services.rules.aggregator import (
    EVAL_WINDOW_DAYS,
    AggregatedMetrics,
    aggregate_rows,
)
from app.services.rules.dispatch import dispatch_action

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Condition evaluation (operates on AggregatedMetrics)
# -------------------------------------------------------------------

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
    fn = _OPS.get(operator)
    if fn is None:
        logger.warning("rules: unknown operator %r", operator)
        return False
    return fn(value, threshold)


def _eval_full_condition(
    agg: AggregatedMetrics, condition: dict
) -> bool:
    """Evaluate a condition tree against aggregated metrics."""
    metric_name = condition.get("metric", "")
    operator = condition.get("operator", "")
    threshold = condition.get("value")

    if not metric_name or not operator or threshold is None:
        return False

    value = agg.get(metric_name)
    if value is None:
        return False

    if not _eval_condition(float(value), operator, float(threshold)):
        return False

    for sub in condition.get("and", []):
        if not _eval_full_condition(agg, sub):
            return False

    or_conditions = condition.get("or", [])
    if or_conditions:
        if not any(
            _eval_full_condition(agg, s) for s in or_conditions
        ):
            return False

    return True


def _build_snapshot(
    agg: AggregatedMetrics, condition: dict
) -> dict:
    """Collect metric values referenced in a condition tree."""
    snap: dict = {"ad_id": str(agg.ad_id)}
    name = condition.get("metric", "")
    if name:
        snap[name] = agg.get(name)
    for sub in condition.get("and", []):
        n = sub.get("metric", "")
        if n:
            snap[n] = agg.get(n)
    for sub in condition.get("or", []):
        n = sub.get("metric", "")
        if n:
            snap[n] = agg.get(n)
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
    """Evaluate all enabled rules against aggregated ad metrics."""
    horizon = datetime.now(timezone.utc) - timedelta(
        days=EVAL_WINDOW_DAYS
    )

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

    # Pull all daily metric rows within the window
    metrics_result = await db.execute(
        select(AdMetric)
        .where(
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= horizon,
        )
        .order_by(AdMetric.ad_id, AdMetric.timestamp.desc())
    )
    all_metrics = list(metrics_result.scalars().all())

    # Group by ad_id and aggregate
    by_ad: dict[uuid.UUID, list[AdMetric]] = {}
    for m in all_metrics:
        by_ad.setdefault(m.ad_id, []).append(m)

    aggregated: dict[uuid.UUID, AggregatedMetrics] = {}
    for ad_id, rows in by_ad.items():
        aggregated[ad_id] = aggregate_rows(rows)

    logger.info(
        "rules: account %s — %d ads in %d-day window",
        account_id, len(aggregated), EVAL_WINDOW_DAYS,
    )

    # Only evaluate ACTIVE ads
    active_ad_ids: set[uuid.UUID] = set()
    if aggregated:
        ads_result = await db.execute(
            select(Ad.id, Ad.status).where(
                Ad.account_id == account_id,
                Ad.id.in_(list(aggregated.keys())),
            )
        )
        for row in ads_result:
            if row[1] == "ACTIVE":
                active_ad_ids.add(row[0])

    actions_taken: list[dict] = []

    for rule in rules:
        try:
            condition = json.loads(rule.condition_json)
            action_cfg = json.loads(rule.action_json)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error(
                "rules: bad JSON in rule %s — %s", rule.id, exc
            )
            continue

        if await check_cooldown(db, rule.id, rule.cooldown_minutes):
            continue

        if (
            rule.budget_limit is not None
            and rule.budget_spent >= rule.budget_limit
        ):
            continue

        for ad_id, agg in aggregated.items():
            if ad_id not in active_ad_ids:
                continue

            if not _eval_full_condition(agg, condition):
                continue

            ad = await db.get(Ad, ad_id)
            if ad is None or ad.account_id != account_id:
                continue

            snapshot = _build_snapshot(agg, condition)
            result = await dispatch_action(
                db, rule, ad, action_cfg, snapshot
            )
            if result:
                ad_spend = agg.get("spend") or 0.0
                rule.budget_spent = (
                    (rule.budget_spent or 0.0) + ad_spend
                )
                await db.flush()
                actions_taken.append(result)
                break  # cooldown: one fire per rule per eval

    logger.info(
        "rules: account %s — %d action(s) from %d rule(s)",
        account_id, len(actions_taken), len(rules),
    )
    return actions_taken
