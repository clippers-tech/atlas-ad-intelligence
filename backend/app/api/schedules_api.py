"""Schedule logs API — track ATLAS Scheduler activity."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schedule_log import ScheduleLog
from app.schemas.schedule_schemas import (
    ScheduleLogCreate,
    ScheduleLogUpdate,
    ScheduleLogResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_schedule_logs(
    limit: int = Query(50, ge=1, le=200),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List recent schedule logs, newest first."""
    q = select(ScheduleLog).order_by(
        ScheduleLog.started_at.desc()
    )
    if status:
        q = q.where(ScheduleLog.status == status)
    q = q.limit(limit)

    result = await db.execute(q)
    logs = result.scalars().all()

    total_q = select(sa_func.count(ScheduleLog.id))
    if status:
        total_q = total_q.where(ScheduleLog.status == status)
    total = (await db.execute(total_q)).scalar() or 0

    return {
        "data": [
            ScheduleLogResponse.model_validate(log).model_dump()
            for log in logs
        ],
        "meta": {"total": total, "limit": limit},
    }


@router.get("/stats")
async def schedule_stats(
    db: AsyncSession = Depends(get_db),
):
    """Aggregated stats per task name for the automation dashboard."""
    q = select(
        ScheduleLog.task_name,
        sa_func.count(ScheduleLog.id).label("total_runs"),
        sa_func.count(
            sa_func.nullif(ScheduleLog.status, "failed")
        ).label("success_count"),
        sa_func.max(ScheduleLog.started_at).label("last_run_at"),
    ).group_by(ScheduleLog.task_name)
    result = await db.execute(q)
    rows = result.all()

    # Also get last status per task
    stats = []
    for row in rows:
        last_q = (
            select(ScheduleLog.status, ScheduleLog.summary)
            .where(ScheduleLog.task_name == row.task_name)
            .order_by(ScheduleLog.started_at.desc())
            .limit(1)
        )
        last = (await db.execute(last_q)).first()
        stats.append({
            "task_name": row.task_name,
            "total_runs": row.total_runs,
            "success_count": row.success_count,
            "fail_count": row.total_runs - row.success_count,
            "last_run_at": row.last_run_at.isoformat()
            if row.last_run_at else None,
            "last_status": last.status if last else None,
            "last_summary": last.summary if last else None,
        })
    return {"data": stats}


@router.post("", status_code=201)
async def create_schedule_log(
    payload: ScheduleLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new schedule log entry (called by Scheduler)."""
    log = ScheduleLog(
        task_name=payload.task_name,
        status=payload.status,
        source=payload.source,
        summary=payload.summary,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return {
        "data": ScheduleLogResponse.model_validate(log).model_dump()
    }


@router.patch("/{log_id}")
async def update_schedule_log(
    log_id: str,
    payload: ScheduleLogUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a schedule log (mark completed/failed)."""
    result = await db.execute(
        select(ScheduleLog).where(ScheduleLog.id == log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Log not found")

    if payload.status is not None:
        log.status = payload.status
    if payload.summary is not None:
        log.summary = payload.summary
    if payload.error_message is not None:
        log.error_message = payload.error_message
    if payload.duration_ms is not None:
        log.duration_ms = payload.duration_ms
    if payload.finished_at is not None:
        log.finished_at = payload.finished_at
    elif payload.status in ("completed", "failed"):
        log.finished_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(log)
    return {
        "data": ScheduleLogResponse.model_validate(log).model_dump()
    }
