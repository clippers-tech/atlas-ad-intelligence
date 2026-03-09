"""Check Meta ad review status and identify newly disapproved ads."""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ad import Ad
from app.services.meta.client import meta_client

logger = logging.getLogger(__name__)

_AD_FIELDS = "id,name,review_feedback,effective_status"


async def check_review_status(
    db: AsyncSession,
    account_id: uuid.UUID,
    meta_ad_account_id: str,
) -> list[dict[str, Any]]:
    """Fetch ad review statuses, update DB records, and return disapproved ads.

    Args:
        db: Async database session.
        account_id: ATLAS account UUID.
        meta_ad_account_id: Meta ad account ID string (e.g. "act_123456").

    Returns:
        List of dicts describing newly disapproved ads, each with keys:
        meta_ad_id, name, reject_reasons.
    """
    logger.info("review_status: checking ads for account %s (%s)", account_id, meta_ad_account_id)
    disapproved: list[dict[str, Any]] = []

    async for page in meta_client.paginate(
        f"/{meta_ad_account_id}/ads",
        params={"fields": _AD_FIELDS, "limit": 200},
    ):
        for raw in page.get("data", []):
            meta_ad_id: str = raw.get("id", "")
            review_feedback = raw.get("review_feedback") or {}
            global_status = review_feedback.get("global", "")

            # Normalise: Meta returns various forms — lowercase for consistency
            review_status = global_status.lower() if global_status else "approved"

            # Fetch local record
            result = await db.execute(
                select(Ad).where(Ad.meta_ad_id == meta_ad_id).limit(1)
            )
            ad = result.scalar_one_or_none()

            if ad is None:
                logger.debug("review_status: no local ad for %s, skipping", meta_ad_id)
                continue

            previous_status = ad.review_status
            ad.review_status = review_status

            if review_status == "disapproved" and previous_status != "disapproved":
                reject_reasons = []
                if isinstance(review_feedback, dict):
                    # Meta nests reasons under summary keys
                    for _key, messages in review_feedback.items():
                        if isinstance(messages, list):
                            reject_reasons.extend(messages)
                        elif isinstance(messages, str) and _key != "global":
                            reject_reasons.append(messages)

                logger.warning(
                    "review_status: ad %s ('%s') newly DISAPPROVED — reasons: %s",
                    meta_ad_id,
                    ad.name,
                    reject_reasons,
                )
                disapproved.append(
                    {
                        "meta_ad_id": meta_ad_id,
                        "name": ad.name,
                        "reject_reasons": reject_reasons,
                        "account_id": str(account_id),
                    }
                )

    await db.commit()
    logger.info(
        "review_status: found %d newly disapproved ads for account %s",
        len(disapproved),
        account_id,
    )
    return disapproved
