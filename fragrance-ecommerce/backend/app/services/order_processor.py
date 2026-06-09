from __future__ import annotations
import random
import string
from decimal import Decimal
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.order import Order, OrderItem
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.order import OrderCreate


def _generate_order_number() -> str:
    suffix = "".join(random.choices(string.digits, k=6))
    return f"SCN-{suffix}"


async def create_order(db: AsyncSession, payload: OrderCreate) -> Order:
    subtotal = Decimal("0")
    order_items = []

    for item_data in payload.items:
        line_total = item_data.unit_price * item_data.quantity - item_data.discount_amount
        subtotal += line_total
        order_items.append(OrderItem(
            product_id=item_data.product_id,
            variant_id=item_data.variant_id,
            sku=item_data.sku,
            name=item_data.name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            supplier_cost=item_data.supplier_cost,
            discount_amount=item_data.discount_amount,
            total=line_total,
        ))

    supplier_cost_total = sum(i.supplier_cost * i.quantity for i in order_items)
    total = subtotal + payload.shipping_amount + payload.tax_amount - payload.discount_amount
    profit = total - supplier_cost_total - payload.shipping_amount

    customer_name = None
    if payload.shipping_address:
        addr = payload.shipping_address
        customer_name = f"{addr.first_name} {addr.last_name}".strip()

    order = Order(
        order_number=_generate_order_number(),
        customer_id=payload.customer_id,
        guest_email=payload.guest_email,
        customer_name=customer_name,
        channel=payload.channel,
        subtotal=subtotal,
        shipping_amount=payload.shipping_amount,
        tax_amount=payload.tax_amount,
        discount_amount=payload.discount_amount,
        total=total,
        currency=payload.currency,
        supplier_cost_total=supplier_cost_total,
        profit_amount=profit,
        shipping_address=payload.shipping_address.model_dump() if payload.shipping_address else None,
        billing_address=payload.billing_address.model_dump() if payload.billing_address else None,
        payment_method=payload.payment_method,
        discount_code=payload.discount_code,
        customer_note=payload.customer_note,
        items=order_items,
    )
    db.add(order)
    await db.flush()

    if payload.customer_id:
        await db.execute(
            update(Customer)
            .where(Customer.id == payload.customer_id)
            .values(
                order_count=Customer.order_count + 1,
                total_spent=Customer.total_spent + total,
            )
        )

    return order


async def update_order_status(
    db: AsyncSession,
    order: Order,
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    fulfillment_status: Optional[str] = None,
) -> Order:
    if status:
        order.status = status
    if payment_status:
        order.payment_status = payment_status
    if fulfillment_status:
        order.fulfillment_status = fulfillment_status
    db.add(order)
    await db.flush()
    return order
