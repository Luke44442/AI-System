"""Discount code validation — money-critical, must stay correct."""
import types
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.discount import DiscountError, resolve_discount


def _dt(offset_days: int = 0) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=offset_days)).isoformat()


def _make_db(discount_obj=None):
    """Async DB session mock that returns discount_obj from execute().scalar_one_or_none()."""
    from unittest.mock import AsyncMock, MagicMock

    scalar_result = MagicMock()
    scalar_result.scalar_one_or_none.return_value = discount_obj
    db = AsyncMock()
    db.execute.return_value = scalar_result
    return db


def make_discount(**overrides):
    base = dict(
        code="SAVE10",
        is_active=True,
        starts_at=None,
        expires_at=None,
        usage_limit=None,
        usage_count=0,
        min_order_amount=None,
        discount_type="percentage",
        discount_value=Decimal("10"),
        max_discount_amount=None,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# Rejection cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_code_raises():
    db = _make_db(None)
    with pytest.raises(DiscountError):
        await resolve_discount(db, "", Decimal("100"))


@pytest.mark.asyncio
async def test_unknown_code_raises():
    db = _make_db(None)
    with pytest.raises(DiscountError, match="Invalid or inactive"):
        await resolve_discount(db, "NOTREAL", Decimal("100"))


@pytest.mark.asyncio
async def test_inactive_code_raises():
    db = _make_db(make_discount(is_active=False))
    with pytest.raises(DiscountError, match="Invalid or inactive"):
        await resolve_discount(db, "SAVE10", Decimal("100"))


@pytest.mark.asyncio
async def test_expired_code_raises():
    db = _make_db(make_discount(expires_at=_dt(-1)))
    with pytest.raises(DiscountError, match="expired"):
        await resolve_discount(db, "SAVE10", Decimal("100"))


@pytest.mark.asyncio
async def test_not_yet_active_raises():
    db = _make_db(make_discount(starts_at=_dt(+1)))
    with pytest.raises(DiscountError, match="not active yet"):
        await resolve_discount(db, "SAVE10", Decimal("100"))


@pytest.mark.asyncio
async def test_usage_limit_exhausted_raises():
    db = _make_db(make_discount(usage_limit=5, usage_count=5))
    with pytest.raises(DiscountError, match="usage limit"):
        await resolve_discount(db, "SAVE10", Decimal("100"))


@pytest.mark.asyncio
async def test_min_order_not_met_raises():
    db = _make_db(make_discount(min_order_amount=Decimal("50")))
    with pytest.raises(DiscountError, match="at least"):
        await resolve_discount(db, "SAVE10", Decimal("30"))


# ---------------------------------------------------------------------------
# Amount calculation cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_percentage_discount():
    # 10% of 200.00 = 20.00
    db = _make_db(make_discount(discount_type="percentage", discount_value=Decimal("10")))
    _, amount = await resolve_discount(db, "SAVE10", Decimal("200"))
    assert amount == Decimal("20.00")


@pytest.mark.asyncio
async def test_fixed_discount():
    db = _make_db(make_discount(discount_type="fixed", discount_value=Decimal("15")))
    _, amount = await resolve_discount(db, "SAVE10", Decimal("200"))
    assert amount == Decimal("15.00")


@pytest.mark.asyncio
async def test_max_cap_applied():
    # 50% of 200 = 100, but capped at 30
    db = _make_db(make_discount(
        discount_type="percentage",
        discount_value=Decimal("50"),
        max_discount_amount=Decimal("30"),
    ))
    _, amount = await resolve_discount(db, "SAVE10", Decimal("200"))
    assert amount == Decimal("30.00")


@pytest.mark.asyncio
async def test_discount_never_exceeds_subtotal():
    # Fixed $200 discount on a $50 order — must be capped at subtotal.
    db = _make_db(make_discount(discount_type="fixed", discount_value=Decimal("200")))
    _, amount = await resolve_discount(db, "SAVE10", Decimal("50"))
    assert amount == Decimal("50.00")


@pytest.mark.asyncio
async def test_code_normalized_to_upper():
    """resolve_discount strips and upper-cases the code; the mock returns a hit."""
    db = _make_db(make_discount())
    discount, amount = await resolve_discount(db, "  save10  ", Decimal("100"))
    assert discount is not None
    assert amount == Decimal("10.00")
