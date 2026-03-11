"""Competitor fetch API — trigger Ad Library pulls per competitor."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.competitor_config import CompetitorConfig
from app.services.competitor.ad_library import (
    AdLibraryError,
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
    db: AsyncSession = Depends(get_db),
):
    """Fetch ads from Meta Ad Library for a specific competitor.

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
        )
    except AdLibraryError as exc:
        logger.error(
            "ad_library_fetch failed for %s: %s (code=%d sub=%d)",
            competitor_id, str(exc), exc.code, exc.subcode,
        )
        # Return helpful error for identity verification issue
        if exc.subcode == 2332002:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Ad Library API access not enabled. "
                    "Complete identity verification at "
                    "facebook.com/ID then visit "
                    "facebook.com/ads/library/api to activate."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ad Library API error: {str(exc)}",
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
        "ad_library_fetch complete for %s: %s", competitor_id, result
    )
    return {"status": "ok", **result}


@router.post("/fetch-all")
async def fetch_all_competitor_ads(
    account_id: UUID = Query(...),
    country: str = Query("ALL"),
    db: AsyncSession = Depends(get_db),
):
    """Fetch ads for ALL competitors in an account that have a page ID."""
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
            "message": "No competitors with Meta Page IDs found.",
            "results": [],
        }

    results = []
    for config in configs:
        try:
            ads_data = await fetch_page_ads(
                page_id=config.meta_page_id,  # type: ignore
                country=country,
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
        except AdLibraryError as exc:
            results.append({
                "competitor_id": str(config.id),
                "competitor_name": config.competitor_name,
                "status": "error",
                "error": str(exc),
            })

    logger.info("fetch_all complete: %d competitors processed", len(results))
    return {"status": "ok", "results": results}
