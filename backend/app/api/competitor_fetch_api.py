"""Competitor fetch API — Apify Ad Library scraper integration.

Two-phase async flow:
1. POST /{id}/fetch — starts Apify run, returns run_id immediately
2. GET /{id}/fetch-status?run_id=X — checks if done, ingests results
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.competitor_config import CompetitorConfig
from app.services.competitor.apify_scraper import (
    ApifyScraperError,
    check_run_status,
    get_run_results,
    start_run,
)
from app.services.competitor.scraper import ingest_competitor_ads

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_config(
    competitor_id: UUID, account_id: UUID, db: AsyncSession
) -> CompetitorConfig:
    """Fetch and validate a competitor config."""
    config = (
        await db.execute(
            select(CompetitorConfig).where(
                CompetitorConfig.id == competitor_id,
                CompetitorConfig.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found for this account.",
        )
    if not config.meta_page_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Meta Page ID. Add one to fetch ads.",
        )
    return config


@router.post("/{competitor_id}/fetch")
async def start_competitor_fetch(
    competitor_id: UUID,
    account_id: UUID = Query(...),
    country: str = Query("ALL"),
    max_ads: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Start an Apify scraper run for a competitor's ads.

    Returns immediately with run_id. Poll /fetch-status to check
    when results are ready.
    """
    config = await _get_config(competitor_id, account_id, db)

    try:
        run_info = await start_run(
            page_id=config.meta_page_id,  # type: ignore
            country=country,
            max_ads=max_ads,
        )
    except ApifyScraperError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Apify error: {str(exc)}",
        )

    return {
        "status": "started",
        "run_id": run_info["run_id"],
        "dataset_id": run_info["dataset_id"],
        "message": "Scraper started. Poll /fetch-status to check progress.",
    }


@router.get("/{competitor_id}/fetch-status")
async def check_competitor_fetch(
    competitor_id: UUID,
    run_id: str = Query(...),
    account_id: UUID = Query(...),
    max_ads: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Check Apify run status. If SUCCEEDED, ingest ads automatically."""
    config = await _get_config(competitor_id, account_id, db)

    try:
        status_info = await check_run_status(run_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to check run: {str(exc)}",
        )

    run_status = status_info["status"]
    dataset_id = status_info.get("dataset_id", "")

    # If still running, return status only
    if run_status in ("RUNNING", "READY"):
        return {"status": "running", "run_id": run_id}

    # If failed, return error
    if run_status in ("FAILED", "ABORTED", "TIMED-OUT"):
        return {"status": "failed", "run_id": run_id, "error": run_status}

    # SUCCEEDED — fetch and ingest results
    if run_status == "SUCCEEDED" and dataset_id:
        try:
            ads_data = await get_run_results(dataset_id, max_ads)
        except ApifyScraperError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to get results: {str(exc)}",
            )

        if not ads_data:
            return {
                "status": "completed",
                "run_id": run_id,
                "new_ads_found": 0,
                "updated": 0,
                "total": 0,
            }

        result = await ingest_competitor_ads(
            db, account_id, competitor_id, ads_data
        )
        logger.info(
            "apify ingest done for %s: %s", competitor_id, result
        )
        return {"status": "completed", "run_id": run_id, **result}

    return {"status": run_status, "run_id": run_id}


@router.post("/fetch-all")
async def start_all_competitor_fetches(
    account_id: UUID = Query(...),
    country: str = Query("ALL"),
    max_ads: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Start Apify runs for ALL competitors with a page ID."""
    configs = (
        await db.execute(
            select(CompetitorConfig).where(
                CompetitorConfig.account_id == account_id,
                CompetitorConfig.is_active == True,
                CompetitorConfig.meta_page_id.isnot(None),
                CompetitorConfig.meta_page_id != "",
            )
        )
    ).scalars().all()

    if not configs:
        return {"status": "ok", "message": "No competitors with Page IDs.", "runs": []}

    runs = []
    for config in configs:
        try:
            run_info = await start_run(
                page_id=config.meta_page_id,  # type: ignore
                country=country,
                max_ads=max_ads,
            )
            runs.append({
                "competitor_id": str(config.id),
                "competitor_name": config.competitor_name,
                "status": "started",
                **run_info,
            })
        except ApifyScraperError as exc:
            runs.append({
                "competitor_id": str(config.id),
                "competitor_name": config.competitor_name,
                "status": "error",
                "error": str(exc),
            })

    return {"status": "ok", "runs": runs}
