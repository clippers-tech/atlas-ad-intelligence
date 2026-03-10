"""Insights API — list and create AI-generated insights."""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.insight import Insight

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
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
            "response_text": None,
            "recommendations_json": None,
            "created_at": r.created_at.isoformat(),
        })

    return {
        "data": data,
        "meta": {"total": total, "page": 1, "per_page": limit},
    }
