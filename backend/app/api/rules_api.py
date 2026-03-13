"""Rules API — manage automation rules."""

import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.account import Account
from app.models.rule import Rule
from app.schemas.rule_schemas import RuleCreate, RuleResponse, RuleUpdate
from app.services.rules.engine import evaluate_rules_for_account

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_rules(
    account_id: UUID = Query(...),
    rule_type: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated rules for an account."""
    base_q = select(Rule).where(Rule.account_id == account_id)
    count_q = select(func.count(Rule.id)).where(Rule.account_id == account_id)

    if rule_type:
        base_q = base_q.where(Rule.type == rule_type)
        count_q = count_q.where(Rule.type == rule_type)
    if is_enabled is not None:
        base_q = base_q.where(Rule.is_enabled == is_enabled)
        count_q = count_q.where(Rule.is_enabled == is_enabled)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * per_page
    rows = (
        await db.execute(
            base_q.order_by(Rule.priority.desc(), Rule.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
    ).scalars().all()

    items = []
    for row in rows:
        item = RuleResponse.model_validate(row).model_dump()
        # Parse JSON string fields if stored as strings
        for field in ("condition_json", "action_json"):
            if isinstance(item.get(field), str):
                try:
                    item[field] = json.loads(item[field])
                except (ValueError, TypeError):
                    pass
        items.append(item)

    return {"data": items, "meta": {"total": total, "page": page, "per_page": per_page}}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new automation rule."""
    rule = Rule(
        account_id=payload.account_id,
        name=payload.name,
        description=payload.description,
        type=payload.type,
        condition_json=json.dumps(payload.condition_json),
        action_json=json.dumps(payload.action_json),
        is_enabled=payload.is_enabled,
        priority=payload.priority,
        cooldown_minutes=payload.cooldown_minutes,
        budget_limit=payload.budget_limit,
        budget_spent=0.0,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    logger.info("Created rule id=%s name=%s", rule.id, rule.name)
    return RuleResponse.model_validate(rule).model_dump()


@router.patch("/{rule_id}")
async def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing rule."""
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field in ("condition_json", "action_json"):
        if field in update_data and isinstance(update_data[field], dict):
            update_data[field] = json.dumps(update_data[field])

    for field, value in update_data.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    logger.info("Updated rule id=%s", rule_id)
    return RuleResponse.model_validate(rule).model_dump()


@router.post("/evaluate")
async def evaluate_rules(
    account_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Run rule evaluation for one or all accounts.

    If account_id is provided, evaluates only that account.
    Otherwise evaluates all active accounts.
    """
    if account_id:
        acct = await db.get(Account, account_id)
        if not acct:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Account not found")
        accounts = [acct]
    else:
        result = await db.execute(
            select(Account).where(Account.is_active.is_(True))
        )
        accounts = list(result.scalars().all())

    all_actions: list[dict] = []
    errors: list[dict] = []

    for acct in accounts:
        try:
            actions = await evaluate_rules_for_account(db, acct.id)
            all_actions.extend(actions)
        except Exception as exc:
            logger.error("evaluate: failed for %s — %s", acct.name, exc)
            errors.append({"account": acct.name, "error": str(exc)})

    await db.commit()
    return {
        "data": {
            "actions_taken": all_actions,
            "total_actions": len(all_actions),
            "accounts_evaluated": len(accounts),
            "errors": errors,
        }
    }


@router.delete("/{rule_id}", status_code=status.HTTP_200_OK)
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a rule."""
    result = await db.execute(select(Rule).where(Rule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found.")

    await db.delete(rule)
    await db.commit()
    logger.info("Deleted rule id=%s name=%s", rule_id, rule.name)
    return {"status": "deleted", "rule_id": str(rule_id)}
