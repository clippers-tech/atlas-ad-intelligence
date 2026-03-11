"""Competitors API — manage watch list, ingest ads, view summaries."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.competitor_ad import CompetitorAd
from app.models.competitor_config import CompetitorConfig
from app.schemas.competitor_schemas import (
    CompetitorAdResponse,
    CompetitorAdsIngestRequest,
    CompetitorConfigCreate,
    CompetitorConfigResponse,
    CompetitorSummaryResponse,
)
from app.services.competitor.scraper import (
    get_competitor_summary,
    ingest_competitor_ads,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_competitors(
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Return all competitor configs for an account with latest ads."""
    result = await db.execute(
        select(CompetitorConfig)
        .where(
            CompetitorConfig.account_id == account_id,
            CompetitorConfig.is_active == True,
        )
        .order_by(CompetitorConfig.competitor_name)
    )
    configs = result.scalars().all()

    data = []
    for config in configs:
        ads_result = await db.execute(
            select(CompetitorAd)
            .where(
                CompetitorAd.competitor_config_id == config.id,
                CompetitorAd.is_active == True,
            )
            .order_by(CompetitorAd.last_seen.desc())
            .limit(5)
        )
        ads = ads_result.scalars().all()

        item = CompetitorConfigResponse.model_validate(config).model_dump()
        item["ads"] = [
            CompetitorAdResponse.model_validate(a).model_dump()
            for a in ads
        ]
        total = (
            await db.execute(
                select(func.count(CompetitorAd.id)).where(
                    CompetitorAd.competitor_config_id == config.id
                )
            )
        ).scalar_one() or 0
        item["total_ads"] = total
        data.append(item)

    return {"data": data, "meta": {"total": len(data)}}


@router.get("/summary")
async def competitor_summary(
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Return per-competitor ad counts and date ranges."""
    summaries = await get_competitor_summary(db, account_id)
    return {"data": summaries, "meta": {"total": len(summaries)}}


@router.get("/{competitor_id}/ads")
async def list_competitor_ads(
    competitor_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated ads for a specific competitor."""
    config = (
        await db.execute(
            select(CompetitorConfig)
            .where(CompetitorConfig.id == competitor_id)
        )
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found.",
        )

    count = (
        await db.execute(
            select(func.count(CompetitorAd.id)).where(
                CompetitorAd.competitor_config_id == competitor_id
            )
        )
    ).scalar_one() or 0

    offset = (page - 1) * per_page
    ads = (
        await db.execute(
            select(CompetitorAd)
            .where(CompetitorAd.competitor_config_id == competitor_id)
            .order_by(CompetitorAd.last_seen.desc())
            .offset(offset)
            .limit(per_page)
        )
    ).scalars().all()

    return {
        "data": [
            CompetitorAdResponse.model_validate(a).model_dump()
            for a in ads
        ],
        "meta": {"total": count, "page": page, "per_page": per_page},
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_competitor(
    payload: CompetitorConfigCreate,
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Add a new competitor to watch."""
    config = CompetitorConfig(
        account_id=account_id,
        competitor_name=payload.competitor_name,
        meta_page_id=payload.meta_page_id,
        website_url=payload.website_url,
        facebook_url=payload.facebook_url,
        scraper_country=payload.scraper_country,
        scraper_media_type=payload.scraper_media_type,
        scraper_platforms=payload.scraper_platforms,
        scraper_language=payload.scraper_language,
        is_active=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    logger.info(
        "Added competitor id=%s name=%s", config.id, config.competitor_name
    )
    return CompetitorConfigResponse.model_validate(config).model_dump()


@router.post("/ads", status_code=status.HTTP_201_CREATED)
async def ingest_ads(
    payload: CompetitorAdsIngestRequest,
    account_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Ingest competitor ads from external source (Ad Library)."""
    config = (
        await db.execute(
            select(CompetitorConfig).where(
                CompetitorConfig.id == payload.competitor_config_id,
                CompetitorConfig.account_id == account_id,
            )
        )
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor config not found for this account.",
        )

    ads_data = [ad.model_dump() for ad in payload.ads]
    result = await ingest_competitor_ads(
        db, account_id, payload.competitor_config_id, ads_data
    )
    logger.info(
        "Ingested ads for competitor %s: %s",
        payload.competitor_config_id,
        result,
    )
    return result


@router.delete("/{competitor_id}", status_code=status.HTTP_200_OK)
async def remove_competitor(
    competitor_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a competitor config by marking it inactive."""
    result = await db.execute(
        select(CompetitorConfig)
        .where(CompetitorConfig.id == competitor_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found.",
        )

    config.is_active = False
    await db.commit()
    logger.info("Removed competitor id=%s", competitor_id)
    return {"status": "ok", "competitor_id": str(competitor_id)}
