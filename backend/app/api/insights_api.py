"""Insights API — list, create, and manage AI-generated insights."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.insight import Insight

logger = logging.getLogger(__name__)
router = APIRouter()


class InsightCreate(BaseModel):
    account_id: str
    type: str = "general"
    title: str
    summary: str
    recommendation: Optional[str] = None
    priority: str = "medium"
    source: str = "claude"


@router.get("")
async def list_insights(
    account_id: str = Query(...),
    type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List insights for an account, newest first."""
    q = (
        select(Insight)
        .where(Insight.account_id == account_id)
        .order_by(Insight.created_at.desc())
        .limit(limit)
    )
    if type:
        q = q.where(Insight.type == type)

    result = await db.execute(q)
    rows = result.scalars().all()

    total = (
        await db.execute(
            select(sa_func.count(Insight.id)).where(
                Insight.account_id == account_id
            )
        )
    ).scalar() or 0

    data = []
    for r in rows:
        data.append({
            "id": str(r.id),
            "account_id": str(r.account_id) if r.account_id else None,
            "type": r.type,
            "title": r.title,
            "summary": r.summary,
            "recommendation": r.recommendation,
            "priority": r.priority,
            "source": r.source,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_insight(
    payload: InsightCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new insight (called by Claude AI analysis)."""
    insight = Insight(
        account_id=payload.account_id,
        type=payload.type,
        title=payload.title,
        summary=payload.summary,
        recommendation=payload.recommendation,
        priority=payload.priority,
        source=payload.source,
    )
    db.add(insight)
    await db.flush()
    await db.refresh(insight)
    return {
        "data": {
            "id": str(insight.id),
            "account_id": str(insight.account_id),
            "type": insight.type,
            "title": insight.title,
            "summary": insight.summary,
            "recommendation": insight.recommendation,
            "priority": insight.priority,
            "source": insight.source,
            "created_at": insight.created_at.isoformat(),
        }
    }


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_insights_batch(
    insights: list[InsightCreate],
    db: AsyncSession = Depends(get_db),
):
    """Create multiple insights at once (from a single analysis run)."""
    created = []
    for payload in insights:
        insight = Insight(
            account_id=payload.account_id,
            type=payload.type,
            title=payload.title,
            summary=payload.summary,
            recommendation=payload.recommendation,
            priority=payload.priority,
            source=payload.source,
        )
        db.add(insight)
        await db.flush()
        await db.refresh(insight)
        created.append({
            "id": str(insight.id),
            "type": insight.type,
            "title": insight.title,
            "priority": insight.priority,
        })
    return {"data": created, "count": len(created)}
