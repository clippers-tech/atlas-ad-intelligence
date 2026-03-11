"""Competitor fetch API — Apify Ad Library scraper integration.

Two-phase async flow:
1. POST /{id}/fetch — starts Apify run, returns run_id + cost estimate
2. GET /{id}/fetch-status?run_id=X — checks if done, ingests results

Guardrails:
- max_ads capped by APIFY_MAX_ADS_PER_FETCH (env config, default 50)
- Default fetch size: APIFY_DEFAULT_ADS (env config, default 10)
- Cost estimate returned on every start
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.competitor_config import CompetitorConfig
from app.services.competitor.apify_scraper import (
    ApifyScraperError,
    check_run_status,
    estimate_cost,
    get_run_results,
    start_run,
)
from app.services.competitor.scraper import ingest_competitor_ads

logger = logging.getLogger(__name__)
router = APIRouter()

# Hard max comes from config — API param cannot exceed it
_HARD_MAX = settings.apify_max_ads_per_fetch
_DEFAULT = settings.apify_default_ads


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
    max_ads: int = Query(
        _DEFAULT, ge=1, le=_HARD_MAX,
        description=(
            f"Max ads to fetch. Default {_DEFAULT}, "
            f"hard limit {_HARD_MAX}."
        ),
    ),
    db: AsyncSession = Depends(get_db),
):
    """Start an Apify scraper run for a competitor's ads.

    Returns immediately with run_id and cost estimate.
    Poll /fetch-status to check when results are ready.
    """
    config = await _get_config(competitor_id, account_id, db)

    try:
        run_info = await start_run(
            page_id=config.meta_page_id,
            facebook_url=config.facebook_url,
            country=config.scraper_country or country,
            media_type=config.scraper_media_type or "all",
            platforms=config.scraper_platforms or "facebook,instagram",
            language=config.scraper_language or "en",
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
        "results_limit": run_info["results_limit"],
        "estimated_cost": run_info["estimated_cost"],
        "message": (
            f"Scraper started — fetching up to "
            f"{run_info['results_limit']} ads "
            f"(~${run_info['estimated_cost']:.3f}). "
            f"Poll /fetch-status to check progress."
        ),
    }


@router.get("/{competitor_id}/fetch-status")
async def check_competitor_fetch(
    competitor_id: UUID,
    run_id: str = Query(...),
    account_id: UUID = Query(...),
    max_ads: int = Query(_DEFAULT, ge=1, le=_HARD_MAX),
    db: AsyncSession = Depends(get_db),
):
    """Check Apify run status. Auto-ingests on SUCCEEDED."""
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

    if run_status in ("RUNNING", "READY"):
        return {"status": "running", "run_id": run_id}

    if run_status in ("FAILED", "ABORTED", "TIMED-OUT"):
        return {
            "status": "failed", "run_id": run_id,
            "error": run_status,
        }

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
    max_ads: int = Query(_DEFAULT, ge=1, le=_HARD_MAX),
    db: AsyncSession = Depends(get_db),
):
    """Start Apify runs for ALL active competitors with a page ID.

    Returns cost estimate for the batch.
    """
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
            "message": "No competitors with Page IDs.",
            "runs": [],
            "total_estimated_cost": 0,
        }

    total_cost = 0.0
    runs = []
    for config in configs:
        try:
            run_info = await start_run(
                page_id=config.meta_page_id,
                facebook_url=config.facebook_url,
                country=config.scraper_country or country,
                media_type=config.scraper_media_type or "all",
                platforms=config.scraper_platforms or "facebook,instagram",
                language=config.scraper_language or "en",
                max_ads=max_ads,
            )
            total_cost += run_info["estimated_cost"]
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

    return {
        "status": "ok",
        "runs": runs,
        "total_estimated_cost": round(total_cost, 4),
    }


@router.get("/limits")
async def get_fetch_limits():
    """Return current Apify fetch limits and pricing info."""
    return {
        "default_ads_per_fetch": _DEFAULT,
        "max_ads_per_fetch": _HARD_MAX,
        "cost_per_ad": settings.apify_cost_per_ad,
        "cost_per_1000": round(settings.apify_cost_per_ad * 1000, 2),
    }
