"""Leads API — list, detail, update, and CSV import."""

import csv
import io
import logging
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.deal import Deal
from app.models.lead import Lead
from app.schemas.lead_schemas import LeadResponse, LeadImportRow

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def list_leads(
    account_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    stage: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Paginated lead list with optional filters."""
    base_q = select(Lead).where(Lead.account_id == account_id)
    count_q = select(func.count(Lead.id)).where(Lead.account_id == account_id)

    if utm_campaign:
        base_q = base_q.where(Lead.utm_campaign == utm_campaign)
        count_q = count_q.where(Lead.utm_campaign == utm_campaign)
    if date_from:
        base_q = base_q.where(Lead.created_at >= date_from)
        count_q = count_q.where(Lead.created_at >= date_from)
    if date_to:
        base_q = base_q.where(Lead.created_at <= date_to)
        count_q = count_q.where(Lead.created_at <= date_to)
    # stage filter applies to associated deals
    if stage:
        base_q = base_q.join(Deal, Deal.lead_id == Lead.id).where(Deal.stage == stage)
        count_q = count_q.join(Deal, Deal.lead_id == Lead.id).where(Deal.stage == stage)

    total = (await db.execute(count_q)).scalar_one() or 0
    offset = (page - 1) * per_page
    rows = (
        await db.execute(
            base_q.order_by(Lead.created_at.desc()).offset(offset).limit(per_page)
        )
    ).scalars().all()

    return {
        "data": [LeadResponse.model_validate(r).model_dump() for r in rows],
        "meta": {"total": total, "page": page, "per_page": per_page},
    }


@router.get("/{lead_id}")
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Single lead with full journey: bookings, deals, payments, landing page events."""
    from app.models.booking import Booking
    from app.models.landing_page_event import LandingPageEvent
    from app.models.payment import Payment

    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    bookings = (
        await db.execute(select(Booking).where(Booking.lead_id == lead_id))
    ).scalars().all()

    deals = (
        await db.execute(select(Deal).where(Deal.lead_id == lead_id))
    ).scalars().all()

    payments_rows = []
    for deal in deals:
        prows = (
            await db.execute(select(Payment).where(Payment.deal_id == deal.id))
        ).scalars().all()
        payments_rows.extend(prows)

    lp_events = (
        await db.execute(
            select(LandingPageEvent).where(LandingPageEvent.lead_id == lead_id)
        )
    ).scalars().all()

    return {
        "data": {
            "lead": LeadResponse.model_validate(lead).model_dump(),
            "bookings": [{"id": str(b.id), "status": b.status, "event_at": b.event_at} for b in bookings],
            "deals": [{"id": str(d.id), "stage": d.stage, "revenue": d.revenue} for d in deals],
            "payments": [{"id": str(p.id), "amount": p.amount, "currency": p.currency} for p in payments_rows],
            "landing_page_events": [
                {"url": e.page_url, "scroll": e.scroll_depth_percent, "time": e.time_on_page_seconds}
                for e in lp_events
            ],
        }
    }


@router.patch("/{lead_id}")
async def update_lead(
    lead_id: UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update lead fields. If stage set to closed_won with revenue, also update deal."""
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found.")

    ALLOWED = {"name", "email", "phone", "utm_campaign", "utm_source", "utm_medium"}
    for field in ALLOWED:
        if field in payload:
            setattr(lead, field, payload[field])

    new_stage = payload.get("stage")
    new_revenue = payload.get("revenue")
    if new_stage == "closed_won" and new_revenue is not None:
        deal_result = await db.execute(
            select(Deal).where(Deal.lead_id == lead_id).limit(1)
        )
        deal = deal_result.scalar_one_or_none()
        if deal:
            deal.stage = "closed_won"
            deal.revenue = new_revenue

    await db.commit()
    await db.refresh(lead)
    return {"data": LeadResponse.model_validate(lead).model_dump()}


@router.post("/import")
async def import_leads(
    account_id: UUID = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """CSV upload: match by email, update existing leads' deals, create new leads."""
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))

    created = updated = 0
    errors = []

    for idx, row in enumerate(reader, 1):
        try:
            data = LeadImportRow(**{k.strip().lower(): v for k, v in row.items() if v})
        except Exception as exc:
            errors.append({"row": idx, "error": str(exc)})
            continue

        existing_result = await db.execute(
            select(Lead).where(Lead.account_id == account_id, Lead.email == data.email)
        )
        lead = existing_result.scalar_one_or_none()

        if lead:
            if data.stage == "closed_won" and data.revenue:
                deal_result = await db.execute(
                    select(Deal).where(Deal.lead_id == lead.id).limit(1)
                )
                deal = deal_result.scalar_one_or_none()
                if deal:
                    deal.stage = "closed_won"
                    deal.revenue = data.revenue
            updated += 1
        else:
            new_lead = Lead(
                account_id=account_id,
                email=data.email,
                name=data.name,
            )
            db.add(new_lead)
            await db.flush()
            if data.stage or data.revenue:
                db.add(Deal(
                    lead_id=new_lead.id,
                    account_id=account_id,
                    stage=data.stage or "new",
                    revenue=data.revenue,
                ))
            created += 1

    await db.commit()
    logger.info("CSV import: created=%d updated=%d errors=%d", created, updated, len(errors))
    return {"data": {"created": created, "updated": updated, "errors": errors}}
