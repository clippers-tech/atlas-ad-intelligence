"""Competitor fetch API — trigger Apify Ad Library pulls per competitor."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.competitor_config import CompetitorConfig
from app.services.competitor.apify_scraper import (
    ApifyScraperError,
    fetch_page_ads,
)
from app.services.competitor.scraper import ingest_competitor_ads

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{competitor_id}/fetch")
async def fetch_competitor_ads(
    competitor_id: UUID,
    account_id: UUID = Query(...),
    country: str = Query("ALL"),
    max_ads: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Fetch ads from Meta Ad Library via Apify for a competitor.

    Requires the competitor to have a meta_page_id configured.
    Fetches active ads and ingests them into the competitor_ads table.
    """
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
            detail="Competitor has no Meta Page ID. Add one to fetch ads.",
        )

    try:
        ads_data = await fetch_page_ads(
            page_id=config.meta_page_id,
            country=country,
            max_ads=max_ads,
        )
    except ApifyScraperError as exc:
        logger.error(
            "apify_fetch failed for %s: %s", competitor_id, str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Apify scraper error: {str(exc)}",
        )

    if not ads_data:
        return {
            "status": "ok",
            "message": "No ads found for this page.",
            "new_ads_found": 0,
            "updated": 0,
            "total": 0,
        }

    result = await ingest_competitor_ads(
        db, account_id, competitor_id, ads_data
    )
    logger.info(
        "apify_fetch complete for %s: %s", competitor_id, result
    )
    return {"status": "ok", **result}


@router.post("/fetch-all")
async def fetch_all_competitor_ads(
    account_id: UUID = Query(...),
    country: str = Query("ALL"),
    max_ads: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Fetch ads for ALL competitors with a page ID via Apify."""
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
        return {
            "status": "ok",
            "message": "No competitors with Meta Page IDs.",
            "results": [],
        }

    results = []
    for config in configs:
        try:
            ads_data = await fetch_page_ads(
                page_id=config.meta_page_id,  # type: ignore
                country=country,
                max_ads=max_ads,
            )
            ingest_result = await ingest_competitor_ads(
                db, account_id, config.id, ads_data
            )
            results.append({
                "competitor_id": str(config.id),
                "competitor_name": config.competitor_name,
                "status": "ok",
                **ingest_result,
            })
        except ApifyScraperError as exc:
            results.append({
                "competitor_id": str(config.id),
                "competitor_name": config.competitor_name,
                "status": "error",
                "error": str(exc),
            })

    logger.info(
        "fetch_all complete: %d competitors processed", len(results)
    )
    return {"status": "ok", "results": results}
