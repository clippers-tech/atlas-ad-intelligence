"""Claude / Insights API — list insights and submit on-demand questions."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.claude_insight import ClaudeInsight
from app.schemas.claude_schemas import ClaudeAskRequest, ClaudeInsightResponse

logger = logging.getLogger(__name__)
router = APIRouter()

VALID_INSIGHT_TYPES = {"daily_digest", "weekly_strategy", "on_demand", "creative_analysis", "competitor_analysis"}


@router.get("/insights")
async def list_insights(
    account_id: Optional[UUID] = Query(None),
    insight_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated Claude insights, filterable by account and type."""
    base_q = select(ClaudeInsight)
    count_q = select(func.count(ClaudeInsight.id))

    if account_id:
        base_q = base_q.where(ClaudeInsight.account_id == account_id)
        count_q = count_q.where(ClaudeInsight.account_id == account_id)
    if insight_type and insight_type in VALID_INSIGHT_TYPES:
        base_q = base_q.where(ClaudeInsight.type == insight_type)
        count_q = count_q.where(ClaudeInsight.type == insight_type)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * per_page
    rows = (
        await db.execute(
            base_q.order_by(ClaudeInsight.created_at.desc()).offset(offset).limit(per_page)
        )
    ).scalars().all()

    return {
        "data": [ClaudeInsightResponse.model_validate(r).model_dump() for r in rows],
        "meta": {"total": total, "page": page, "per_page": per_page},
    }


@router.post("/claude/ask", status_code=status.HTTP_202_ACCEPTED)
async def claude_ask(
    payload: ClaudeAskRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an on-demand question to Claude.
    Phase 4: actual Claude API call. For now, stores the question and returns a placeholder.
    """
    insight = ClaudeInsight(
        account_id=payload.account_id,
        type="on_demand",
        prompt_text=payload.question,
        response_text=(
            "Claude integration is coming in Phase 4. "
            "Your question has been queued for processing."
        ),
        model_used="placeholder",
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)

    logger.info(
        "On-demand Claude question stored id=%s account_id=%s",
        insight.id,
        payload.account_id,
    )

    return {
        "status": "queued",
        "insight_id": str(insight.id),
        "message": "Claude integration is Phase 4. Question stored for future processing.",
        "question": payload.question,
    }
