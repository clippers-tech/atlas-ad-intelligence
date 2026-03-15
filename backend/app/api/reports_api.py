"""Reports API — weekly report data assembly.

Reports data is assembled by the backend and consumed by the
ATLAS Scheduler during scheduled runs or manually triggered.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.reports.generator import generate_weekly_report_data

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/data")
async def get_report_data(
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Return structured weekly report data.

    Used by the ATLAS Scheduler during automated runs
    and by the dashboard for report generation.
    """
    data = await generate_weekly_report_data(db, account_id)
    return {"data": data}
