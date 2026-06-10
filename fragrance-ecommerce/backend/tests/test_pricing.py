"""Pricing engine + order profitability — money math regression guard."""
from decimal import Decimal

from app.services.pricing_engine import (
    calculate_website_price, calculate_marketplace_price, calculate_margin,
)
from app.services.pricing_intelligence import calculate_order_profitability


def test_website_price_uses_markup():
    # cost 10 + shipping 8 = 18 * 2.8 = 50.40, above the 40% min-margin floor
    price = calculate_website_price(Decimal("10"), Decimal("8"))
    assert price >= Decimal("50.40")


def test_website_price_respects_min_margin_floor():
    # A tiny markup multiplier should still not drop below the 40% margin floor.
    price = calculate_website_price(Decimal("10"), Decimal("0"), markup_multiplier=Decimal("1.1"))
    floor = Decimal("10") / (Decimal("1") - Decimal("0.40"))
    assert price >= floor


def test_marketplace_price_includes_fees():
    web = calculate_website_price(Decimal("10"), Decimal("8"))
    market = calculate_marketplace_price(Decimal("10"), Decimal("8"), platform="ebay")
    # eBay fee (12%) makes marketplace price strictly higher than website price.
    assert market > web


def test_margin_calculation():
    m = calculate_margin(Decimal("100"), Decimal("30"), Decimal("8"), Decimal("0.029"))
    assert m["total_cost"] == Decimal("38.00")
    assert m["profit"] < Decimal("62")  # fee reduces it
    assert m["margin_pct"] > Decimal("0")


def test_order_profitability_breakdown():
    p = calculate_order_profitability(
        order_total=Decimal("100"), supplier_cost=Decimal("30"),
        shipping_cost=Decimal("8"), channel="website",
    )
    # website has no platform fee, stripe = 2.9% + 0.30
    assert p["platform_fee"] == Decimal("0.00")
    assert p["stripe_fee"] == Decimal("3.20")
    assert p["gross_profit"] == Decimal("62.00")
    assert p["net_profit"] == Decimal("58.80")
    assert p["margin_pct"] > Decimal("0")


def test_order_profitability_etsy_has_platform_fee():
    p = calculate_order_profitability(
        order_total=Decimal("100"), supplier_cost=Decimal("30"),
        shipping_cost=Decimal("8"), channel="etsy",
    )
    assert p["platform_fee"] > Decimal("0")
    # Etsy net profit must be lower than website net profit on identical inputs.
    web = calculate_order_profitability(Decimal("100"), Decimal("30"), Decimal("8"), "website")
    assert p["net_profit"] < web["net_profit"]
