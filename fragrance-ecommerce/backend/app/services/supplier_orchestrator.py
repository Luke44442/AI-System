"""SupplierOrchestrator — guaranteed supplier fulfillment path.

Every paid order is driven to exactly one terminal outcome:

    placed / shipped / delivered  — supplier API accepted the order
    failed                        — with a recorded reason (visible in queue)
    manual_queue                  — explicitly queued for human action

There is no code path that leaves an order silently in "processing".
All transitions emit system_events for the failures dashboard.
"""
from __future__ import annotations
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.order import Order, OrderItem
from app.models.product import Product, Supplier
from app.models.fulfillment import SupplierOrder
from app.services.events import record_event
from app.services.suppliers import get_fulfillment_adapter
from app.services.suppliers.base import (
    SupplierOrderRequest, SupplierOrderItem, SupplierOrderStatus, SupplierAPIError,
)

log = structlog.get_logger("supplier_orchestrator")


def _retry_delays() -> tuple[int, ...]:
    """Exponential backoff (2s, 4s, 8s, ...) sized by SUPPLIER_ORDER_MAX_ATTEMPTS."""
    attempts = max(settings.SUPPLIER_ORDER_MAX_ATTEMPTS, 1)
    return tuple(2 ** i for i in range(1, attempts))


def _normalize_address(addr: Optional[dict]) -> dict:
    """Accept both internal (address1/address2) and adapter (line1/line2) shapes."""
    addr = addr or {}
    return {
        "first_name": addr.get("first_name", ""),
        "last_name": addr.get("last_name", ""),
        "line1": addr.get("line1") or addr.get("address1", ""),
        "line2": addr.get("line2") or addr.get("address2", ""),
        "city": addr.get("city", ""),
        "state": addr.get("state", ""),
        "postal_code": addr.get("postal_code", ""),
        "country": addr.get("country", "US"),
        "phone": addr.get("phone", ""),
    }


async def _get_or_create_supplier_order(db: AsyncSession, order: Order) -> SupplierOrder:
    result = await db.execute(select(SupplierOrder).where(SupplierOrder.order_id == order.id))
    so = result.scalar_one_or_none()
    if so is None:
        so = SupplierOrder(order_id=order.id, supplier_id=order.supplier_id, status="pending")
        db.add(so)
        await db.flush()
    return so


async def _build_request(db: AsyncSession, order: Order) -> tuple[Optional[SupplierOrderRequest], Optional[str]]:
    """Build the supplier order request. Returns (request, error_reason)."""
    items: list[SupplierOrderItem] = []
    missing: list[str] = []
    for item in order.items:
        supplier_sku = item.supplier_sku
        if not supplier_sku and item.product_id:
            row = await db.execute(select(Product.supplier_sku).where(Product.id == item.product_id))
            supplier_sku = row.scalar_one_or_none()
        if not supplier_sku:
            missing.append(item.sku)
            continue
        items.append(SupplierOrderItem(
            supplier_sku=supplier_sku, quantity=item.quantity,
            name=item.name, unit_cost=item.supplier_cost,
        ))
    if missing:
        return None, f"Missing supplier SKU mapping for items: {', '.join(missing)}"
    if not items:
        return None, "Order has no fulfillable items"
    if not order.shipping_address:
        return None, "Order has no shipping address"
    return SupplierOrderRequest(
        order_number=order.order_number,
        items=items,
        shipping_address=_normalize_address(order.shipping_address),
        note=f"Aurevia order {order.order_number}",
    ), None


async def fallback_to_manual_queue(
    db: AsyncSession, order: Order, reason: str,
    supplier_order: Optional[SupplierOrder] = None,
) -> SupplierOrder:
    """Explicitly queue an order for human fulfillment. Always terminal."""
    so = supplier_order or await _get_or_create_supplier_order(db, order)
    so.status = "manual_queue"
    so.queued_reason = reason
    await record_event(
        db, "supplier_order_queued_manual", severity="warning",
        message=reason, order_id=order.id,
        payload={"order_number": order.order_number},
    )
    await db.commit()
    return so


async def place_order(db: AsyncSession, order: Order) -> SupplierOrder:
    """Place the supplier order for a paid order. Idempotent and terminal.

    Safe to call repeatedly: once a SupplierOrder reaches a terminal state it
    is returned unchanged (no duplicate supplier orders).
    """
    so = await _get_or_create_supplier_order(db, order)
    if so.is_terminal:
        return so

    if order.payment_status != "paid":
        return await fallback_to_manual_queue(db, order, "Order is not paid — refusing to order from supplier", so)

    # Resolve supplier + adapter
    supplier: Optional[Supplier] = None
    if order.supplier_id:
        row = await db.execute(select(Supplier).where(Supplier.id == order.supplier_id))
        supplier = row.scalar_one_or_none()
    if supplier is None:
        return await fallback_to_manual_queue(db, order, "No supplier assigned to order", so)
    so.supplier_id = supplier.id

    adapter = get_fulfillment_adapter(supplier.type, supplier.credentials)
    if adapter is None:
        return await fallback_to_manual_queue(
            db, order,
            f"Supplier '{supplier.name}' (type={supplier.type}) has no API adapter or is unconfigured",
            so,
        )

    request, build_error = await _build_request(db, order)
    if build_error:
        return await fallback_to_manual_queue(db, order, build_error, so)

    so.request_payload = {
        "order_number": request.order_number,
        "items": [{"supplier_sku": i.supplier_sku, "quantity": i.quantity} for i in request.items],
    }

    # Retry loop with exponential backoff for transient supplier failures.
    so.status = "placing"
    last_error: Optional[str] = None
    for attempt, delay in enumerate((0,) + _retry_delays(), start=1):
        if delay:
            await asyncio.sleep(delay)
        so.attempts += 1
        so.last_attempt_at = datetime.now(timezone.utc)
        try:
            result = adapter.place_order(request)
        except SupplierAPIError as exc:
            last_error = str(exc)
            await record_event(
                db, "supplier_api_call_failed",
                severity="warning" if exc.retryable else "error",
                message=last_error, order_id=order.id,
                payload={"supplier": supplier.slug, "attempt": so.attempts, "retryable": exc.retryable},
            )
            if not exc.retryable:
                so.status = "failed"
                so.failure_reason = last_error
                so.response_payload = exc.raw
                await record_event(
                    db, "supplier_order_failed", severity="error",
                    message=last_error, order_id=order.id,
                    payload={"supplier": supplier.slug, "attempts": so.attempts},
                )
                await db.commit()
                return so
            continue
        except Exception as exc:  # adapter bug — never leave the order dangling
            last_error = f"Unexpected adapter error: {exc}"
            break

        # Success
        so.status = "placed"
        so.external_order_id = result.external_order_id
        so.external_status = result.external_status
        so.response_payload = result.raw
        so.failure_reason = None
        so.resolved_by = "auto"
        order.supplier_order_id = result.external_order_id
        order.supplier_order_data = {"supplier": supplier.slug, "external_status": result.external_status}
        await record_event(
            db, "supplier_order_placed", severity="info",
            message=f"Supplier order {result.external_order_id} placed with {supplier.name}",
            order_id=order.id,
            payload={"supplier": supplier.slug, "external_order_id": result.external_order_id,
                     "attempts": so.attempts},
        )
        await db.commit()
        return so

    # Retries exhausted (or adapter bug) → failed, visible in the queue.
    so.status = "failed"
    so.failure_reason = f"Supplier order failed after {so.attempts} attempts: {last_error}"
    await record_event(
        db, "supplier_order_failed", severity="critical",
        message=so.failure_reason, order_id=order.id,
        payload={"supplier": supplier.slug, "attempts": so.attempts},
    )
    await db.commit()
    return so


async def track_order(db: AsyncSession, supplier_order: SupplierOrder) -> SupplierOrder:
    """Poll the supplier for status; promote the order when shipped/delivered."""
    if supplier_order.status not in ("placed", "shipped") or not supplier_order.external_order_id:
        return supplier_order

    row = await db.execute(select(Supplier).where(Supplier.id == supplier_order.supplier_id))
    supplier = row.scalar_one_or_none()
    adapter = get_fulfillment_adapter(supplier.type if supplier else None,
                                      supplier.credentials if supplier else None)
    if adapter is None:
        return supplier_order

    try:
        result = adapter.get_order_status(supplier_order.external_order_id)
    except SupplierAPIError as exc:
        await record_event(
            db, "supplier_tracking_failed", severity="warning",
            message=str(exc), order_id=supplier_order.order_id,
            payload={"external_order_id": supplier_order.external_order_id},
        )
        await db.commit()
        return supplier_order

    supplier_order.external_status = result.external_status
    if result.status == SupplierOrderStatus.SHIPPED and supplier_order.status != "shipped":
        supplier_order.status = "shipped"
        supplier_order.tracking_number = result.tracking_number
        supplier_order.carrier = result.carrier
        supplier_order.tracking_url = result.tracking_url
        await record_event(
            db, "supplier_order_shipped", severity="info",
            message=f"Tracking {result.tracking_number} via {result.carrier}",
            order_id=supplier_order.order_id,
        )
        if result.tracking_number:
            order_row = await db.execute(
                select(Order).where(Order.id == supplier_order.order_id)
            )
            order = order_row.scalar_one_or_none()
            if order:
                from app.services.fulfillment import assign_tracking
                # assign_tracking commits and emails the customer.
                await assign_tracking(db, order, result.tracking_number, result.carrier, result.tracking_url)
                return supplier_order
    elif result.status == SupplierOrderStatus.DELIVERED:
        supplier_order.status = "delivered"
        await record_event(db, "supplier_order_delivered", severity="info",
                           order_id=supplier_order.order_id)
    await db.commit()
    return supplier_order


async def resolve_manually(
    db: AsyncSession, supplier_order: SupplierOrder, *,
    external_order_id: Optional[str] = None,
    resolved_by: str = "admin",
    note: Optional[str] = None,
) -> SupplierOrder:
    """Admin marks a queued/failed supplier order as manually placed."""
    supplier_order.status = "placed"
    supplier_order.external_order_id = external_order_id or supplier_order.external_order_id
    supplier_order.failure_reason = None
    supplier_order.resolved_by = resolved_by
    await record_event(
        db, "supplier_order_resolved_manually", severity="info",
        message=note or f"Manually resolved by {resolved_by}",
        order_id=supplier_order.order_id,
        payload={"external_order_id": external_order_id},
    )
    await db.commit()
    return supplier_order


async def retry_supplier_order(db: AsyncSession, supplier_order: SupplierOrder) -> SupplierOrder:
    """Admin retry: re-run placement for a failed/queued supplier order."""
    row = await db.execute(
        select(Order).where(Order.id == supplier_order.order_id)
    )
    order = row.scalar_one_or_none()
    if order is None:
        return supplier_order
    # Re-arm the state machine, then drive to a terminal state again.
    supplier_order.status = "pending"
    supplier_order.failure_reason = None
    supplier_order.queued_reason = None
    await db.flush()
    return await place_order(db, order)
