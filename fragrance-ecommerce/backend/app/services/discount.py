"""Discount code validation and application."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import DiscountCode


class DiscountError(Exception):
    """Raised when a discount code is invalid for the given order."""


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def resolve_discount(db: AsyncSession, code: str, subtotal: Decimal) -> tuple[DiscountCode, Decimal]:
    """Validate a discount code against an order subtotal.

    Returns (discount_code, discount_amount). Raises DiscountError if invalid.
    """
    if not code:
        raise DiscountError("No discount code provided")

    result = await db.execute(select(DiscountCode).where(DiscountCode.code == code.strip().upper()))
    discount = result.scalar_one_or_none()
    if not discount or not discount.is_active:
        raise DiscountError("Invalid or inactive discount code")

    now = datetime.now(timezone.utc)
    starts_at = _parse_dt(discount.starts_at)
    expires_at = _parse_dt(discount.expires_at)
    if starts_at and now < starts_at:
        raise DiscountError("This code is not active yet")
    if expires_at and now > expires_at:
        raise DiscountError("This code has expired")
    if discount.usage_limit is not None and discount.usage_count >= discount.usage_limit:
        raise DiscountError("This code has reached its usage limit")
    if discount.min_order_amount and subtotal < discount.min_order_amount:
        raise DiscountError(f"Order must be at least ${discount.min_order_amount} to use this code")

    if discount.discount_type == "percentage":
        amount = (subtotal * discount.discount_value / Decimal("100"))
    else:  # fixed amount
        amount = discount.discount_value

    if discount.max_discount_amount:
        amount = min(amount, discount.max_discount_amount)
    amount = min(amount, subtotal)  # never exceed subtotal
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return discount, amount
