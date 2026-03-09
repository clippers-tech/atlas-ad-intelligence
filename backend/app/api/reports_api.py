"""Reports API — list generated reports and serve PDFs."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.claude_insight import ClaudeInsight
from app.schemas.claude_schemas import ClaudeInsightResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Report types that are treated as "reports" (vs ad-hoc insights)
REPORT_TYPES = ("weekly_strategy", "daily_digest")


@router.get("")
async def list_reports(
    account_id: Optional[UUID] = Query(None),
    report_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List generated reports.
    Reports are stored as ClaudeInsight entries of type weekly_strategy or daily_digest.
    """
    base_q = select(ClaudeInsight).where(ClaudeInsight.type.in_(REPORT_TYPES))
    count_q = select(func.count(ClaudeInsight.id)).where(ClaudeInsight.type.in_(REPORT_TYPES))

    if account_id:
        base_q = base_q.where(ClaudeInsight.account_id == account_id)
        count_q = count_q.where(ClaudeInsight.account_id == account_id)
    if report_type and report_type in REPORT_TYPES:
        base_q = base_q.where(ClaudeInsight.type == report_type)
        count_q = count_q.where(ClaudeInsight.type == report_type)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * per_page
    rows = (
        await db.execute(
            base_q.order_by(ClaudeInsight.created_at.desc()).offset(offset).limit(per_page)
        )
    ).scalars().all()

    items = []
    for row in rows:
        item = ClaudeInsightResponse.model_validate(row).model_dump()
        item["download_url"] = f"/api/reports/{row.id}/download"
        items.append(item)

    return {
        "data": items,
        "meta": {"total": total, "page": page, "per_page": per_page},
    }


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Serve a report PDF.
    Phase 4: PDFs will be generated and stored in S3.
    For now, returns a placeholder response.
    """
    result = await db.execute(
        select(ClaudeInsight).where(
            ClaudeInsight.id == report_id,
            ClaudeInsight.type.in_(REPORT_TYPES),
        )
    )
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")

    # Phase 4: check for a stored PDF path and serve via FileResponse
    # pdf_path = insight.pdf_path  # future field
    # if pdf_path and os.path.exists(pdf_path):
    #     return FileResponse(pdf_path, media_type="application/pdf", filename=f"report_{report_id}.pdf")

    logger.info("PDF download requested for report id=%s (placeholder)", report_id)

    return {
        "status": "pending",
        "report_id": str(report_id),
        "type": insight.type,
        "created_at": insight.created_at.isoformat(),
        "message": "PDF generation is Phase 4. Report text is available in the data field.",
        "content_preview": (insight.response_text or "")[:500],
    }
