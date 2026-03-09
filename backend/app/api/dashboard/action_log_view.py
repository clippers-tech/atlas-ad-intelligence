"""Dashboard action log — list and undo automated actions."""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.action_log import ActionLog
from app.schemas.action_log_schemas import ActionLogResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/actions")
async def list_action_logs(
    account_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    action_type: Optional[str] = Query(None),
    triggered_by: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated action log entries with optional filters."""

    base_q = select(ActionLog).where(ActionLog.account_id == account_id)
    count_q = select(func.count(ActionLog.id)).where(ActionLog.account_id == account_id)

    if action_type:
        base_q = base_q.where(ActionLog.action_type == action_type)
        count_q = count_q.where(ActionLog.action_type == action_type)
    if triggered_by:
        base_q = base_q.where(ActionLog.triggered_by == triggered_by)
        count_q = count_q.where(ActionLog.triggered_by == triggered_by)

    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * per_page
    rows_result = await db.execute(
        base_q.order_by(ActionLog.created_at.desc()).offset(offset).limit(per_page)
    )
    rows = rows_result.scalars().all()

    items = []
    for row in rows:
        item = ActionLogResponse.model_validate(row).model_dump()
        # Parse details_json if stored as string
        if isinstance(item.get("details_json"), str):
            try:
                item["details_json"] = json.loads(item["details_json"])
            except (ValueError, TypeError):
                pass
        items.append(item)

    return {
        "data": items,
        "meta": {"total": total, "page": page, "per_page": per_page},
    }


@router.post("/actions/{action_id}/undo", status_code=status.HTTP_200_OK)
async def undo_action(
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark an action as reversed.
    Actual reversal (e.g., re-enabling a paused ad via Meta API) is handled
    by the rule engine background task — this endpoint flags intent.
    """
    result = await db.execute(select(ActionLog).where(ActionLog.id == action_id))
    action = result.scalar_one_or_none()

    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found.")

    if not action.is_reversible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This action is not reversible.",
        )

    if action.reversed_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Action has already been reversed.",
        )

    action.reversed_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("Action id=%s marked for reversal", action_id)
    return {
        "status": "ok",
        "action_id": str(action_id),
        "reversed_at": action.reversed_at.isoformat(),
        "message": "Action flagged for reversal. Background task will apply the change.",
    }
