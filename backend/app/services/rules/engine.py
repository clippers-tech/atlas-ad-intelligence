"""Rules engine — evaluates automation rules against ad metrics and fires actions."""

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_log import ActionLog
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.rule import Rule
from app.services.meta.actions import pause_ad, resume_ad, update_budget

logger = logging.getLogger(__name__)

_OPS: dict = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
}


def _eval_condition(value: float, operator: str, threshold: float) -> bool:
    """Evaluate a single numeric condition against a threshold."""
    fn = _OPS.get(operator)
    if fn is None:
        logger.warning("rules_engine: unknown operator %r", operator)
        return False
    return fn(value, threshold)


def _metric_from_row(row: AdMetric, metric_name: str) -> float | None:
    """Extract a named metric value from an AdMetric row, or None if absent."""
    return getattr(row, metric_name, None)


# ---------------------------------------------------------------------------
# Cooldown check
# ---------------------------------------------------------------------------

async def check_cooldown(
    db: AsyncSession, rule_id: uuid.UUID, cooldown_minutes: int
) -> bool:
    """Return True if the rule fired recently and is still in cooldown."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
    result = await db.execute(
        select(ActionLog.created_at)
        .where(
            ActionLog.rule_id == rule_id,
            ActionLog.created_at >= cutoff,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

async def _dispatch_action(
    db: AsyncSession,
    rule: Rule,
    ad: Ad,
    action_cfg: dict,
    metric_snapshot: dict,
) -> dict | None:
    """Execute the configured action and write an ActionLog entry."""
    action_name: str = action_cfg.get("action", "")
    percent: float = float(action_cfg.get("percent", 10))
    result: dict | None = None
    action_type: str = action_name
    is_reversible = True

    if action_name == "pause":
        result = await pause_ad(ad.meta_ad_id)
        action_type = "pause"
        is_reversible = True

    elif action_name == "resume":
        result = await resume_ad(ad.meta_ad_id)
        action_type = "resume"
        is_reversible = True

    elif action_name in ("increase_budget", "decrease_budget"):
        # Operate on the parent AdSet budget
        adset_row = await db.get(AdSet, ad.ad_set_id)
        if adset_row is None:
            logger.warning("rules_engine: adset %s not found for ad %s", ad.ad_set_id, ad.id)
            return None
        current = adset_row.daily_budget or 0.0
        if action_name == "increase_budget":
            new_budget = current * (1 + percent / 100)
            action_type = "increase_budget"
        else:
            new_budget = current * (1 - percent / 100)
            action_type = "decrease_budget"
        result = await update_budget(adset_row.meta_adset_id, new_budget)
        is_reversible = True

    else:
        logger.warning("rules_engine: unhandled action %r for rule %s", action_name, rule.id)
        return None

    if result is None or not result.get("success"):
        logger.error(
            "rules_engine: action %s failed for ad %s — %s",
            action_type, ad.meta_ad_id, result,
        )
        return None

    # Persist to action_log
    log_entry = ActionLog(
        account_id=rule.account_id,
        ad_id=ad.id,
        rule_id=rule.id,
        action_type=action_type,
        details_json=json.dumps({
            "rule_name": rule.name,
            "metric_snapshot": metric_snapshot,
            "meta_result": result,
        }),
        is_reversible=is_reversible,
        triggered_by="rule_engine",
    )
    db.add(log_entry)
    await db.flush()

    logger.info(
        "rules_engine: rule %r fired action %s on ad %s",
        rule.name, action_type, ad.meta_ad_id,
    )
    return {
        "rule_id": str(rule.id),
        "rule_name": rule.name,
        "ad_id": str(ad.id),
        "meta_ad_id": ad.meta_ad_id,
        "action": action_type,
        "metric_snapshot": metric_snapshot,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def evaluate_rules_for_account(
    db: AsyncSession, account_id: uuid.UUID
) -> list[dict]:
    """Evaluate all active rules for the account and execute triggered actions."""
    horizon = datetime.now(timezone.utc) - timedelta(hours=1)

    # Load all enabled rules for this account
    rules_result = await db.execute(
        select(Rule).where(
            Rule.account_id == account_id,
            Rule.is_enabled.is_(True),
        ).order_by(Rule.priority.desc())
    )
    rules: list[Rule] = list(rules_result.scalars().all())

    if not rules:
        logger.debug("rules_engine: no active rules for account %s", account_id)
        return []

    # Fetch recent metrics (all ads, last hour)
    metrics_result = await db.execute(
        select(AdMetric)
        .where(
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= horizon,
        )
        .order_by(AdMetric.ad_id, AdMetric.timestamp.desc())
    )
    all_metrics: list[AdMetric] = list(metrics_result.scalars().all())

    # Group by ad_id — keep most recent per ad
    latest_by_ad: dict[uuid.UUID, AdMetric] = {}
    for m in all_metrics:
        if m.ad_id not in latest_by_ad:
            latest_by_ad[m.ad_id] = m

    actions_taken: list[dict] = []

    for rule in rules:
        try:
            condition: dict = json.loads(rule.condition_json)
            action_cfg: dict = json.loads(rule.action_json)
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error("rules_engine: invalid JSON in rule %s — %s", rule.id, exc)
            continue

        metric_name: str = condition.get("metric", "")
        operator: str = condition.get("operator", "")
        threshold = condition.get("value")

        if not metric_name or not operator or threshold is None:
            logger.warning("rules_engine: incomplete condition in rule %s — skipping", rule.id)
            continue

        # Check cooldown once per rule (not per-ad)
        in_cooldown = await check_cooldown(db, rule.id, rule.cooldown_minutes)
        if in_cooldown:
            logger.debug("rules_engine: rule %r is in cooldown — skipping", rule.name)
            continue

        for ad_id, metric_row in latest_by_ad.items():
            metric_value = _metric_from_row(metric_row, metric_name)
            if metric_value is None:
                continue

            if not _eval_condition(float(metric_value), operator, float(threshold)):
                continue

            ad = await db.get(Ad, ad_id)
            if ad is None or ad.account_id != account_id:
                continue

            snapshot = {metric_name: metric_value, "ad_id": str(ad_id)}
            action_result = await _dispatch_action(db, rule, ad, action_cfg, snapshot)
            if action_result:
                actions_taken.append(action_result)
                # Enforce cooldown: once fired, stop evaluating further ads for this rule
                break

    logger.info(
        "rules_engine: account %s — %d action(s) taken from %d rule(s)",
        account_id, len(actions_taken), len(rules),
    )
    return actions_taken
