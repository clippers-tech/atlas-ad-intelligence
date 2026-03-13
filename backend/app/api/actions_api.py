"""Actions API — pause/resume ads, ad sets, campaigns on Meta."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.ad import Ad
from app.models.ad_set import AdSet
from app.models.campaign import Campaign
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)
router = APIRouter()


class StatusToggleRequest(BaseModel):
    status: str  # "ACTIVE" or "PAUSED"


async def _toggle_meta_status(
    meta_id: str, new_status: str
) -> dict:
    """Push status change to Meta API."""
    if new_status not in ("ACTIVE", "PAUSED"):
        raise HTTPException(
            400, f"Invalid status: {new_status}"
        )
    try:
        result = await meta_client.post(
            f"/{meta_id}", {"status": new_status}
        )
        success = bool(result.get("success"))
        return {"success": success, "meta_id": meta_id}
    except Exception as exc:
        logger.error(
            "actions: failed to set %s to %s — %s",
            meta_id, new_status, exc,
        )
        raise HTTPException(
            502, f"Meta API error: {exc}"
        )


@router.post("/ads/{ad_id}/status")
async def toggle_ad_status(
    ad_id: UUID,
    body: StatusToggleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Pause or resume an ad on Meta and update DB."""
    ad = (
        await db.execute(select(Ad).where(Ad.id == ad_id))
    ).scalar_one_or_none()
    if not ad:
        raise HTTPException(404, "Ad not found")

    result = await _toggle_meta_status(
        ad.meta_ad_id, body.status
    )
    await db.execute(
        update(Ad).where(Ad.id == ad_id).values(
            status=body.status
        )
    )
    await db.commit()
    return {
        "success": True,
        "id": str(ad_id),
        "meta_id": ad.meta_ad_id,
        "new_status": body.status,
    }


@router.post("/ad-sets/{adset_id}/status")
async def toggle_adset_status(
    adset_id: UUID,
    body: StatusToggleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Pause or resume an ad set on Meta and update DB."""
    adset = (
        await db.execute(
            select(AdSet).where(AdSet.id == adset_id)
        )
    ).scalar_one_or_none()
    if not adset:
        raise HTTPException(404, "Ad set not found")

    result = await _toggle_meta_status(
        adset.meta_adset_id, body.status
    )
    await db.execute(
        update(AdSet).where(AdSet.id == adset_id).values(
            status=body.status
        )
    )
    await db.commit()
    return {
        "success": True,
        "id": str(adset_id),
        "meta_id": adset.meta_adset_id,
        "new_status": body.status,
    }


@router.post("/campaigns/{campaign_id}/status")
async def toggle_campaign_status(
    campaign_id: UUID,
    body: StatusToggleRequest,
    db: AsyncSession = Depends(get_db),
):
    """Pause or resume a campaign on Meta and update DB."""
    camp = (
        await db.execute(
            select(Campaign).where(
                Campaign.id == campaign_id
            )
        )
    ).scalar_one_or_none()
    if not camp:
        raise HTTPException(404, "Campaign not found")

    result = await _toggle_meta_status(
        camp.meta_campaign_id, body.status
    )
    await db.execute(
        update(Campaign)
        .where(Campaign.id == campaign_id)
        .values(status=body.status)
    )
    await db.commit()
    return {
        "success": True,
        "id": str(campaign_id),
        "meta_id": camp.meta_campaign_id,
        "new_status": body.status,
    }
