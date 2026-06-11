"""Order fulfillment workflow.

Pipeline: paid order → verify → assign supplier → enter fulfillment queue →
(later) tracking assignment → customer notification.

`process_paid_order` runs the automated portion synchronously when a payment
succeeds; tracking assignment is completed by an admin (or supplier sync) via
`assign_tracking`.
"""
from __future__ import annotations
import logging
from collections import Counter
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.analytics import OrderProfitability
from app.services.events import record_event
from app.services.pricing_intelligence import calculate_order_profitability
from app.services.email import (
    send_order_confirmation_email,
    send_shipping_notification_email,
)

logger = logging.getLogger(__name__)


def _dispatch_supplier_order(order_id) -> str:
    """Queue supplier ordering via Celery; report how it was dispatched.

    Returns 'queued' on success, 'inline_required' when the broker is down so
    the caller can run the orchestrator inline instead of dropping the order.
    """
    try:
        from app.workers.tasks import place_supplier_order_task
        place_supplier_order_task.delay(str(order_id))
        return "queued"
    except Exception as exc:
        logger.error("supplier_order_dispatch_failed order=%s error=%s", order_id, exc)
        return "inline_required"


async def _assign_supplier(db: AsyncSession, order: Order) -> None:
    """Assign the order to the supplier that fulfills most of its line items."""
    product_ids = [i.product_id for i in order.items if i.product_id]
    if not product_ids:
        return
    rows = await db.execute(select(Product.id, Product.supplier_id).where(Product.id.in_(product_ids)))
    supplier_by_product = {pid: sid for pid, sid in rows.all()}
    counts = Counter(sid for sid in supplier_by_product.values() if sid)
    if counts:
        order.supplier_id = counts.most_common(1)[0][0]


async def _record_profitability(db: AsyncSession, order: Order) -> OrderProfitability | None:
    """Create or update the OrderProfitability row for this order."""
    existing = await db.execute(select(OrderProfitability).where(OrderProfitability.order_id == order.id))
    row = existing.scalar_one_or_none()

    breakdown = calculate_order_profitability(
        order_total=order.total,
        supplier_cost=order.supplier_cost_total or Decimal("0"),
        shipping_cost=order.shipping_amount or Decimal("0"),
        channel=order.channel or "website",
    )
    if row is None:
        row = OrderProfitability(order_id=order.id, **breakdown)
        db.add(row)
    else:
        for k, v in breakdown.items():
            setattr(row, k, v)
    return row


async def process_paid_order(db: AsyncSession, order: Order) -> dict:
    """Run the automated fulfillment pipeline for a freshly-paid order."""
    if order.payment_status != "paid":
        return {"order_id": str(order.id), "skipped": "not paid"}

    # 1. Verify → 2. Assign supplier
    await _assign_supplier(db, order)

    # 3. Enter fulfillment queue
    if order.fulfillment_status in (None, "unfulfilled"):
        order.fulfillment_status = "processing"
    if order.status in ("pending_payment", "confirmed"):
        order.status = "processing"

    # 4. Record profitability snapshot for analytics
    await _record_profitability(db, order)

    await record_event(
        db, "order_fulfillment_started", severity="info",
        message=f"Order {order.order_number} entered fulfillment",
        order_id=order.id,
        payload={"supplier_id": str(order.supplier_id) if order.supplier_id else None},
    )
    await db.commit()

    # 5. Place the supplier order — async via Celery, inline if the broker is
    # down. Either way the order is guaranteed to reach a terminal supplier
    # state (placed / failed / manual_queue); nothing stops at "processing".
    dispatch = _dispatch_supplier_order(order.id)
    if dispatch == "inline_required":
        from app.services.supplier_orchestrator import place_order as place_supplier_order
        await place_supplier_order(db, order)

    # 6. Customer notification (best-effort)
    recipient = order.guest_email or (order.customer.email if order.customer else None)
    if recipient:
        try:
            first_name = (order.customer.first_name if order.customer else None) or order.customer_name
            items = [
                {"name": i.name, "quantity": i.quantity, "unit_price": float(i.unit_price)}
                for i in order.items
            ]
            send_order_confirmation_email(
                to=recipient,
                first_name=first_name,
                order_number=order.order_number,
                items=items,
                subtotal=float(order.subtotal),
                shipping=float(order.shipping_amount),
                tax=float(order.tax_amount),
                discount=float(order.discount_amount),
                total=float(order.total),
                shipping_address=order.shipping_address,
            )
        except Exception:
            pass

    logger.info("order_fulfillment_processed order=%s supplier=%s", order.order_number, order.supplier_id)
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "fulfillment_status": order.fulfillment_status,
        "supplier_id": str(order.supplier_id) if order.supplier_id else None,
    }


async def assign_tracking(db: AsyncSession, order: Order, tracking_number: str,
                          carrier: str | None = None, tracking_url: str | None = None) -> dict:
    """Attach tracking to an order, mark it shipped, and notify the customer."""
    order.tracking_number = tracking_number
    order.carrier = carrier
    order.tracking_url = tracking_url
    order.fulfillment_status = "shipped"
    if order.status == "processing":
        order.status = "shipped"
    await record_event(
        db, "order_shipped", severity="info",
        message=f"Order {order.order_number} shipped via {carrier or 'carrier'} ({tracking_number})",
        order_id=order.id,
        payload={"tracking_number": tracking_number, "carrier": carrier},
    )
    await db.commit()

    recipient = order.guest_email or (order.customer.email if order.customer else None)
    if recipient:
        try:
            first_name = (order.customer.first_name if order.customer else None) or order.customer_name
            send_shipping_notification_email(
                to=recipient,
                first_name=first_name,
                order_number=order.order_number,
                tracking_number=tracking_number,
                tracking_url=tracking_url,
                carrier=carrier,
            )
        except Exception:
            pass
    return {"order_id": str(order.id), "fulfillment_status": "shipped", "tracking_number": tracking_number}
