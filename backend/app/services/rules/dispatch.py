"""Action dispatch — execute rule actions and log to action_log."""

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_log import ActionLog
from app.models.ad import Ad
from app.models.ad_set import AdSet
from app.models.rule import Rule
from app.services.meta.actions import pause_ad, resume_ad, update_budget

logger = logging.getLogger(__name__)


async def dispatch_action(
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

    elif action_name == "resume":
        result = await resume_ad(ad.meta_ad_id)
        action_type = "resume"

    elif action_name in ("increase_budget", "decrease_budget"):
        adset_row = await db.get(AdSet, ad.ad_set_id)
        if adset_row is None:
            logger.warning(
                "dispatch: adset %s not found for ad %s",
                ad.ad_set_id, ad.id,
            )
            return None
        current = adset_row.daily_budget or 0.0
        if action_name == "increase_budget":
            new_budget = current * (1 + percent / 100)
        else:
            new_budget = current * (1 - percent / 100)
        action_type = action_name
        result = await update_budget(
            adset_row.meta_adset_id, new_budget
        )

    elif action_name == "notify":
        return await _log_alert(
            db, rule, ad, metric_snapshot
        )

    else:
        logger.warning(
            "dispatch: unhandled action %r for rule %s",
            action_name, rule.id,
        )
        return None

    if result is None or not result.get("success"):
        logger.error(
            "dispatch: action %s failed for ad %s — %s",
            action_type, ad.meta_ad_id, result,
        )
        return None

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
        "dispatch: rule %r fired %s on ad %s",
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


async def _log_alert(
    db: AsyncSession,
    rule: Rule,
    ad: Ad,
    metric_snapshot: dict,
) -> dict:
    """Log an alert-type action (no Meta API call)."""
    logger.info(
        "dispatch: ALERT rule %r triggered for ad %s",
        rule.name, ad.meta_ad_id,
    )
    log_entry = ActionLog(
        account_id=rule.account_id,
        ad_id=ad.id,
        rule_id=rule.id,
        action_type="alert",
        details_json=json.dumps({
            "rule_name": rule.name,
            "metric_snapshot": metric_snapshot,
            "alert": True,
        }),
        is_reversible=False,
        triggered_by="rule_engine",
    )
    db.add(log_entry)
    await db.flush()
    return {
        "rule_id": str(rule.id),
        "rule_name": rule.name,
        "ad_id": str(ad.id),
        "meta_ad_id": ad.meta_ad_id,
        "action": "alert",
        "metric_snapshot": metric_snapshot,
    }
