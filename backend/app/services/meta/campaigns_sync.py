"""Sync Meta campaigns → ad sets → ads into the ATLAS database.

Upserts all entities matching on meta_campaign_id / meta_adset_id / meta_ad_id.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.models.ad_set import AdSet
from app.models.campaign import Campaign
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

_CAMPAIGN_FIELDS = "id,name,objective,status,daily_budget,lifetime_budget"
_ADSET_FIELDS = "id,name,status,daily_budget,targeting,audience_type"
_AD_FIELDS = "id,name,status,creative{id,thumbnail_url}"


async def _upsert_campaign(
    db: AsyncSession, account_id: uuid.UUID, raw: dict[str, Any]
) -> Campaign:
    result = await db.execute(
        select(Campaign).where(Campaign.meta_campaign_id == raw["id"])
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        campaign = Campaign(account_id=account_id, meta_campaign_id=raw["id"])
        db.add(campaign)
    campaign.name = raw.get("name", "")
    campaign.objective = raw.get("objective")
    campaign.status = raw.get("status", "UNKNOWN")
    daily = raw.get("daily_budget")
    campaign.daily_budget = float(daily) / 100 if daily else None
    lifetime = raw.get("lifetime_budget")
    campaign.lifetime_budget = float(lifetime) / 100 if lifetime else None
    return campaign


async def _upsert_adset(
    db: AsyncSession,
    account_id: uuid.UUID,
    campaign: Campaign,
    raw: dict[str, Any],
) -> AdSet:
    result = await db.execute(
        select(AdSet).where(AdSet.meta_adset_id == raw["id"])
    )
    adset = result.scalar_one_or_none()
    if adset is None:
        adset = AdSet(account_id=account_id, campaign_id=campaign.id, meta_adset_id=raw["id"])
        db.add(adset)
    adset.name = raw.get("name", "")
    adset.status = raw.get("status", "UNKNOWN")
    daily = raw.get("daily_budget")
    adset.daily_budget = float(daily) / 100 if daily else None
    return adset


async def _upsert_ad(
    db: AsyncSession,
    account_id: uuid.UUID,
    adset: AdSet,
    raw: dict[str, Any],
) -> Ad:
    result = await db.execute(select(Ad).where(Ad.meta_ad_id == raw["id"]))
    ad = result.scalar_one_or_none()
    if ad is None:
        ad = Ad(account_id=account_id, ad_set_id=adset.id, meta_ad_id=raw["id"])
        db.add(ad)
    ad.name = raw.get("name", "")
    ad.status = raw.get("status", "UNKNOWN")
    creative = raw.get("creative") or {}
    ad.thumbnail_url = creative.get("thumbnail_url")
    return ad


async def sync_campaigns(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
) -> None:
    """Fetch and upsert campaigns → adsets → ads for one Meta ad account."""
    logger.info("campaigns_sync: starting for account %s (%s)", account_id, meta_ad_account_id)
    campaign_count = adset_count = ad_count = 0

    async for campaign_page in meta_client.paginate(
        f"/{meta_ad_account_id}/campaigns",
        params={"fields": _CAMPAIGN_FIELDS, "limit": 100},
    ):
        for raw_campaign in campaign_page.get("data", []):
            campaign = await _upsert_campaign(db, account_id, raw_campaign)
            await db.flush()
            campaign_count += 1

            try:
                async for adset_page in meta_client.paginate(
                    f"/{raw_campaign['id']}/adsets",
                    params={"fields": _ADSET_FIELDS, "limit": 100},
                ):
                    for raw_adset in adset_page.get("data", []):
                        adset = await _upsert_adset(db, account_id, campaign, raw_adset)
                        await db.flush()
                        adset_count += 1

                        try:
                            async for ad_page in meta_client.paginate(
                                f"/{raw_adset['id']}/ads",
                                params={"fields": _AD_FIELDS, "limit": 100},
                            ):
                                for raw_ad in ad_page.get("data", []):
                                    await _upsert_ad(db, account_id, adset, raw_ad)
                                    ad_count += 1
                        except Exception as exc:
                            logger.warning("campaigns_sync: ads fetch failed for adset %s — %s", raw_adset['id'], exc)
            except Exception as exc:
                logger.warning("campaigns_sync: adsets fetch failed for campaign %s — %s", raw_campaign['id'], exc)

    await db.commit()
    logger.info(
        "campaigns_sync: done — %d campaigns, %d adsets, %d ads for account %s",
        campaign_count, adset_count, ad_count, account_id,
    )
