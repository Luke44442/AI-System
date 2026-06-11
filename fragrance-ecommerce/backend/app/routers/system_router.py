"""System observability + human-fallback control center (admin only).

This is deliberately a FAILURES dashboard, not analytics: it answers
"what needs a human right now?" — failed supplier orders, the manual
supplier queue, dead-lettered listings, and recent error events.
"""
from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_admin
from app.database import get_db
from app.models.order import Order
from app.models.marketplace import MarketplaceListing
from app.models.fulfillment import SupplierOrder, SystemEvent, MarketplaceDeadLetter

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(get_current_admin)])


def _supplier_order_dict(so: SupplierOrder, order: Optional[Order] = None) -> dict:
    return {
        "id": str(so.id),
        "order_id": str(so.order_id),
        "order_number": order.order_number if order else None,
        "order_total": str(order.total) if order else None,
        "customer_name": order.customer_name if order else None,
        "supplier_id": str(so.supplier_id) if so.supplier_id else None,
        "status": so.status,
        "external_order_id": so.external_order_id,
        "external_status": so.external_status,
        "tracking_number": so.tracking_number,
        "failure_reason": so.failure_reason,
        "queued_reason": so.queued_reason,
        "attempts": so.attempts,
        "last_attempt_at": so.last_attempt_at.isoformat() if so.last_attempt_at else None,
        "created_at": so.created_at.isoformat() if so.created_at else None,
    }


@router.get("/failures")
async def failures_dashboard(db: AsyncSession = Depends(get_db)):
    """Everything that's broken or waiting for a human, in one response."""
    failed_supplier = (await db.execute(
        select(func.count()).select_from(SupplierOrder).where(SupplierOrder.status == "failed")
    )).scalar_one()
    manual_queue = (await db.execute(
        select(func.count()).select_from(SupplierOrder).where(SupplierOrder.status == "manual_queue")
    )).scalar_one()
    dead_listings = (await db.execute(
        select(func.count()).select_from(MarketplaceDeadLetter)
        .where(MarketplaceDeadLetter.is_resolved == False)  # noqa: E712
    )).scalar_one()
    retrying_listings = (await db.execute(
        select(func.count()).select_from(MarketplaceListing)
        .where(MarketplaceListing.status == "retrying")
    )).scalar_one()
    # Paid orders with no supplier order at all = the old silent gap.
    orphaned = (await db.execute(
        select(func.count()).select_from(Order)
        .outerjoin(SupplierOrder, SupplierOrder.order_id == Order.id)
        .where(Order.payment_status == "paid",
               Order.fulfillment_status.in_(["unfulfilled", "processing"]),
               SupplierOrder.id.is_(None))
    )).scalar_one()

    recent_errors = (await db.execute(
        select(SystemEvent)
        .where(SystemEvent.severity.in_(["error", "critical"]))
        .order_by(SystemEvent.created_at.desc())
        .limit(25)
    )).scalars().all()

    return {
        "counts": {
            "failed_supplier_orders": failed_supplier,
            "supplier_queue_backlog": manual_queue,
            "dead_letter_listings": dead_listings,
            "retrying_listings": retrying_listings,
            "orphaned_paid_orders": orphaned,
        },
        "healthy": (failed_supplier + manual_queue + dead_listings + orphaned) == 0,
        "recent_errors": [
            {"id": str(e.id), "event_type": e.event_type, "severity": e.severity,
             "message": e.message, "order_id": str(e.order_id) if e.order_id else None,
             "listing_id": str(e.listing_id) if e.listing_id else None,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in recent_errors
        ],
    }


@router.get("/events")
async def list_events(
    severity: Optional[str] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    order_id: Optional[uuid.UUID] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(SystemEvent)
    if severity:
        query = query.where(SystemEvent.severity == severity)
    if event_type:
        query = query.where(SystemEvent.event_type == event_type)
    if order_id:
        query = query.where(SystemEvent.order_id == order_id)
    rows = await db.execute(query.order_by(SystemEvent.created_at.desc()).limit(limit))
    return {
        "items": [
            {"id": str(e.id), "event_type": e.event_type, "severity": e.severity,
             "message": e.message, "payload": e.payload,
             "order_id": str(e.order_id) if e.order_id else None,
             "listing_id": str(e.listing_id) if e.listing_id else None,
             "product_id": str(e.product_id) if e.product_id else None,
             "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in rows.scalars().all()
        ]
    }


# ---------------------------------------------------------------------------
# Supplier queue — the human fallback control center
# ---------------------------------------------------------------------------

@router.get("/supplier-queue")
async def supplier_queue(
    status: Optional[str] = Query(default=None, description="manual_queue|failed|placed|shipped"),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(SupplierOrder, Order).join(Order, Order.id == SupplierOrder.order_id)
    if status:
        query = query.where(SupplierOrder.status == status)
    else:
        query = query.where(SupplierOrder.status.in_(["manual_queue", "failed", "placing", "pending"]))
    rows = await db.execute(query.order_by(SupplierOrder.created_at.asc()).limit(limit))
    items = [_supplier_order_dict(so, order) for so, order in rows.all()]
    return {"items": items, "count": len(items)}


class ResolveRequest(BaseModel):
    external_order_id: Optional[str] = None
    note: Optional[str] = None


@router.post("/supplier-queue/{supplier_order_id}/retry")
async def retry_queue_item(supplier_order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Re-run automated placement for a failed/queued supplier order."""
    from app.services.supplier_orchestrator import retry_supplier_order
    row = await db.execute(select(SupplierOrder).where(SupplierOrder.id == supplier_order_id))
    so = row.scalar_one_or_none()
    if not so:
        raise HTTPException(status_code=404, detail="Supplier order not found")
    if so.status in ("placed", "shipped", "delivered"):
        raise HTTPException(status_code=409, detail=f"Already {so.status} — nothing to retry")
    so = await retry_supplier_order(db, so)
    return _supplier_order_dict(so)


@router.post("/supplier-queue/{supplier_order_id}/resolve")
async def resolve_queue_item(
    supplier_order_id: uuid.UUID,
    payload: ResolveRequest,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a queued/failed supplier order as manually placed by a human."""
    from app.services.supplier_orchestrator import resolve_manually
    row = await db.execute(select(SupplierOrder).where(SupplierOrder.id == supplier_order_id))
    so = row.scalar_one_or_none()
    if not so:
        raise HTTPException(status_code=404, detail="Supplier order not found")
    so = await resolve_manually(
        db, so,
        external_order_id=payload.external_order_id,
        resolved_by=getattr(admin, "email", "admin"),
        note=payload.note,
    )
    return _supplier_order_dict(so)


# ---------------------------------------------------------------------------
# Dead-letter management
# ---------------------------------------------------------------------------

@router.get("/dead-letters")
async def list_dead_letters(
    include_resolved: bool = Query(default=False),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(MarketplaceDeadLetter)
    if not include_resolved:
        query = query.where(MarketplaceDeadLetter.is_resolved == False)  # noqa: E712
    rows = await db.execute(query.order_by(MarketplaceDeadLetter.created_at.desc()).limit(limit))
    return {
        "items": [
            {"id": str(d.id), "listing_id": str(d.listing_id) if d.listing_id else None,
             "product_id": str(d.product_id) if d.product_id else None,
             "platform": d.platform, "operation": d.operation, "attempts": d.attempts,
             "last_error": d.last_error, "payload": d.payload, "is_resolved": d.is_resolved,
             "created_at": d.created_at.isoformat() if d.created_at else None}
            for d in rows.scalars().all()
        ]
    }


@router.post("/dead-letters/{dead_letter_id}/retry")
async def retry_dead_letter(dead_letter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Reset the listing's retry budget and re-sync it immediately."""
    from app.models.product import Product
    from app.services.marketplaces.service import sync_product_to_platform

    row = await db.execute(select(MarketplaceDeadLetter).where(MarketplaceDeadLetter.id == dead_letter_id))
    dl = row.scalar_one_or_none()
    if not dl:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    if not dl.product_id:
        raise HTTPException(status_code=409, detail="Dead letter has no product to re-sync")

    listing_row = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == dl.listing_id)
    )
    listing = listing_row.scalar_one_or_none()
    if listing:
        listing.sync_attempts = 0
        listing.status = "retrying"

    prod_row = await db.execute(
        select(Product).where(Product.id == dl.product_id).options(selectinload(Product.brand))
    )
    product = prod_row.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    result = await sync_product_to_platform(db, product, dl.platform)
    if result.status.value == "success":
        dl.is_resolved = True
        await db.commit()
    return {"status": result.status.value, "message": result.message, "resolved": dl.is_resolved}


@router.post("/dead-letters/{dead_letter_id}/resolve")
async def resolve_dead_letter(dead_letter_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    row = await db.execute(select(MarketplaceDeadLetter).where(MarketplaceDeadLetter.id == dead_letter_id))
    dl = row.scalar_one_or_none()
    if not dl:
        raise HTTPException(status_code=404, detail="Dead letter not found")
    dl.is_resolved = True
    await db.commit()
    return {"id": str(dl.id), "is_resolved": True}
