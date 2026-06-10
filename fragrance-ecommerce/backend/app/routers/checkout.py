from __future__ import annotations
import uuid
import stripe
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import settings
from app.database import get_db
from app.models.product import Product
from app.models.order import Order, OrderItem
from app.core.auth import get_optional_user
import structlog

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/checkout", tags=["checkout"])

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class CartLineItem(BaseModel):
    product_id: uuid.UUID
    quantity: int


class CreatePaymentIntentRequest(BaseModel):
    items: List[CartLineItem]
    shipping_address: Optional[dict] = None
    customer_email: Optional[str] = None


class PaymentIntentResponse(BaseModel):
    client_secret: str
    amount: int
    currency: str
    order_id: str
    order_number: str


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    payload: CreatePaymentIntentRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Payment processing not configured")

    product_ids = [item.product_id for item in payload.items]
    result = await db.execute(
        select(Product)
        .where(Product.id.in_(product_ids), Product.is_active == True)
        .options(selectinload(Product.brand))
    )
    products_by_id = {p.id: p for p in result.scalars().all()}

    if len(products_by_id) != len(set(product_ids)):
        missing = [str(pid) for pid in product_ids if pid not in products_by_id]
        raise HTTPException(status_code=404, detail=f"Products not found: {missing}")

    subtotal = Decimal("0")
    order_items_data = []
    for line in payload.items:
        product = products_by_id[line.product_id]
        price = product.website_price or Decimal("0")
        line_total = price * line.quantity
        subtotal += line_total
        brand_name = product.brand.name + " " if product.brand else ""
        order_items_data.append({
            "product_id": product.id,
            "name": f"{brand_name}{product.name}",
            "sku": product.sku,
            "quantity": line.quantity,
            "unit_price": price,
            "total": line_total,
            "supplier_cost": (product.supplier_cost or Decimal("0")) * line.quantity,
        })

    shipping_amount = Decimal("9.99") if subtotal < Decimal("150") else Decimal("0")
    total = subtotal + shipping_amount
    amount_cents = int(total * 100)

    customer_email = (
        payload.customer_email
        or (current_user.email if current_user else None)
        or "guest@aurevia.com"
    )

    order = Order(
        order_number=f"SCN-{uuid.uuid4().hex[:8].upper()}",
        customer_id=current_user.id if current_user else None,
        guest_email=customer_email if not current_user else None,
        subtotal=subtotal,
        shipping_amount=shipping_amount,
        tax_amount=Decimal("0"),
        discount_amount=Decimal("0"),
        total=total,
        currency="USD",
        status="pending_payment",
        payment_status="pending",
        fulfillment_status="unfulfilled",
        payment_provider="stripe",
        shipping_address=payload.shipping_address or {},
        billing_address=payload.shipping_address or {},
    )
    db.add(order)
    await db.flush()

    supplier_cost_total = Decimal("0")
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            name=item_data["name"],
            sku=item_data["sku"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            supplier_cost=item_data["supplier_cost"],
            discount_amount=Decimal("0"),
            total=item_data["total"],
        )
        db.add(order_item)
        supplier_cost_total += item_data["supplier_cost"]

    order.supplier_cost_total = supplier_cost_total
    order.profit_amount = total - supplier_cost_total - shipping_amount

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={
                "order_id": str(order.id),
                "order_number": order.order_number,
            },
            receipt_email=customer_email,
            automatic_payment_methods={"enabled": True},
        )
        order.payment_intent_id = intent.id
        await db.commit()

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            amount=amount_cents,
            currency="usd",
            order_id=str(order.id),
            order_number=order.order_number,
        )
    except stripe.StripeError as e:
        log.error("stripe_error", error=str(e))
        raise HTTPException(status_code=502, detail=f"Payment processing error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    body = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(body, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        order_id = pi.get("metadata", {}).get("order_id")
        if order_id:
            result = await db.execute(select(Order).where(Order.id == uuid.UUID(order_id)))
            order = result.scalar_one_or_none()
            if order:
                order.status = "confirmed"
                order.payment_status = "paid"
                order.payment_intent_id = pi["id"]
                await db.commit()
                log.info("order_payment_confirmed", order_id=order_id)

    elif event["type"] == "payment_intent.payment_failed":
        pi = event["data"]["object"]
        order_id = pi.get("metadata", {}).get("order_id")
        if order_id:
            result = await db.execute(select(Order).where(Order.id == uuid.UUID(order_id)))
            order = result.scalar_one_or_none()
            if order:
                order.payment_status = "failed"
                await db.commit()

    return {"status": "ok"}


@router.get("/order/{order_id}")
async def get_order_status(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user and order.customer_id and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "total": float(order.total),
        "currency": order.currency,
    }
