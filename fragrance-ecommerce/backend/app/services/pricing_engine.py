from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


_TWO = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(_TWO, rounding=ROUND_HALF_UP)


def calculate_website_price(
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    markup_multiplier: Decimal = Decimal("2.8"),
    min_margin_pct: Decimal = Decimal("40"),
) -> Decimal:
    total_cost = supplier_cost + shipping_cost
    price = _round(total_cost * markup_multiplier)
    min_price = _round(total_cost / (1 - min_margin_pct / 100))
    return max(price, min_price)


def calculate_marketplace_price(
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    platform: str = "etsy",
    markup_multiplier: Decimal = Decimal("3.2"),
) -> Decimal:
    platform_fees = {
        "etsy": Decimal("0.065"),
        "ebay": Decimal("0.12"),
        "facebook": Decimal("0.05"),
    }
    fee_rate = platform_fees.get(platform, Decimal("0.10"))
    total_cost = supplier_cost + shipping_cost
    base_price = _round(total_cost * markup_multiplier)
    price_with_fees = _round(base_price / (1 - fee_rate))
    return price_with_fees


def calculate_margin(
    sell_price: Decimal,
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    platform_fee_rate: Decimal = Decimal("0"),
) -> dict:
    total_cost = supplier_cost + shipping_cost
    platform_fee = _round(sell_price * platform_fee_rate)
    net_revenue = sell_price - platform_fee
    profit = net_revenue - total_cost
    margin_pct = _round((profit / sell_price * 100)) if sell_price else Decimal("0")
    return {
        "sell_price": sell_price,
        "total_cost": total_cost,
        "platform_fee": platform_fee,
        "net_revenue": net_revenue,
        "profit": profit,
        "margin_pct": margin_pct,
    }


def apply_pricing_rule(
    base_price: Decimal,
    multiplier: Decimal = Decimal("1"),
    fixed_addition: Decimal = Decimal("0"),
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
) -> Decimal:
    price = _round(base_price * multiplier + fixed_addition)
    if min_price:
        price = max(price, min_price)
    if max_price:
        price = min(price, max_price)
    return price


def bulk_price_products(
    products: list[dict],
    website_multiplier: Decimal = Decimal("2.8"),
    marketplace_multiplier: Decimal = Decimal("3.2"),
) -> list[dict]:
    result = []
    for p in products:
        cost = Decimal(str(p.get("supplier_cost", 0)))
        shipping = Decimal(str(p.get("shipping_cost", 0)))
        result.append({
            **p,
            "website_price": calculate_website_price(cost, shipping, website_multiplier),
            "marketplace_price": calculate_marketplace_price(cost, shipping, multiplier=marketplace_multiplier),
        })
    return result
