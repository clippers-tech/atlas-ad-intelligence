"""Audience test queue management — graduate and kill launched tests."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.ad import Ad
from app.models.ad_metric import AdMetric
from app.models.ad_set import AdSet
from app.models.audience_test_queue import AudienceTestQueue

logger = logging.getLogger(__name__)

_TEST_MIN_DAYS = 7


def _queue_item_dict(item: AudienceTestQueue) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "audience_name": item.audience_name,
        "audience_type": item.audience_type,
        "status": item.status,
        "launched_at": item.launched_at.isoformat() if item.launched_at else None,
    }


async def _get_queue_item_cpl(
    db: AsyncSession,
    account_id: uuid.UUID,
    item: AudienceTestQueue,
) -> float:
    """Derive CPL for an AudienceTestQueue item by matching its ad set name."""
    if not item.launched_at:
        return 0.0

    adset_result = await db.execute(
        select(AdSet.id).where(
            AdSet.account_id == account_id,
            AdSet.name == item.audience_name,
        )
    )
    adset_ids = [row[0] for row in adset_result.all()]
    if not adset_ids:
        return 0.0

    ad_ids_result = await db.execute(
        select(Ad.id).where(
            Ad.ad_set_id.in_(adset_ids),
            Ad.account_id == account_id,
        )
    )
    ad_ids = [row[0] for row in ad_ids_result.all()]
    if not ad_ids:
        return 0.0

    agg = await db.execute(
        select(
            func.sum(AdMetric.spend).label("spend"),
            func.sum(AdMetric.conversions).label("conversions"),
        ).where(
            AdMetric.ad_id.in_(ad_ids),
            AdMetric.account_id == account_id,
            AdMetric.timestamp >= item.launched_at,
        )
    )
    row = agg.one()
    spend = float(row.spend or 0)
    conversions = int(row.conversions or 0)
    return (spend / conversions) if conversions > 0 else 0.0


async def manage_test_queue(
    db: AsyncSession, account_id: uuid.UUID
) -> dict[str, list[dict[str, Any]]]:
    """Evaluate the audience test queue and graduate or kill launched tests.

    Decision logic for items with status="launched" active >7 days:
    - CPL < account.target_cpl  → graduate
    - CPL > 2x account.target_cpl → kill
    - Otherwise → still_testing

    Returns:
        Dict with keys: graduated, killed, still_testing, queued.
    """
    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(days=_TEST_MIN_DAYS)

    acct_result = await db.execute(
        select(Account.target_cpl).where(Account.id == account_id)
    )
    target_cpl: float | None = acct_result.scalar_one_or_none()

    queue_result = await db.execute(
        select(AudienceTestQueue).where(
            AudienceTestQueue.account_id == account_id,
            AudienceTestQueue.status.in_(["queued", "launched"]),
        )
    )
    items = list(queue_result.scalars().all())

    graduated: list[dict[str, Any]] = []
    killed: list[dict[str, Any]] = []
    still_testing: list[dict[str, Any]] = []
    queued: list[dict[str, Any]] = []

    for item in items:
        if item.status == "queued":
            queued.append(_queue_item_dict(item))
            continue

        # launched: check if enough days have passed
        if not item.launched_at or item.launched_at > cutoff:
            still_testing.append(_queue_item_dict(item))
            continue

        cpl = await _get_queue_item_cpl(db, account_id, item)

        if target_cpl and cpl > 0:
            if cpl < target_cpl:
                item.status = "graduated"
                logger.info(
                    "test_queue: item %s graduated (cpl=%.2f < target=%.2f)",
                    item.id, cpl, target_cpl,
                )
                graduated.append({**_queue_item_dict(item), "cpl": round(cpl, 2)})
            elif cpl > target_cpl * 2:
                item.status = "killed"
                item.killed_at = now
                item.kill_reason = f"CPL {cpl:.2f} > 2x target {target_cpl:.2f}"
                logger.info(
                    "test_queue: item %s killed (cpl=%.2f > 2x target=%.2f)",
                    item.id, cpl, target_cpl,
                )
                killed.append({**_queue_item_dict(item), "cpl": round(cpl, 2)})
            else:
                still_testing.append({**_queue_item_dict(item), "cpl": round(cpl, 2)})
        else:
            still_testing.append(_queue_item_dict(item))

    await db.commit()
    logger.info(
        "test_queue: manage — graduated=%d killed=%d still=%d queued=%d",
        len(graduated), len(killed), len(still_testing), len(queued),
    )
    return {
        "graduated": graduated,
        "killed": killed,
        "still_testing": still_testing,
        "queued": queued,
    }
