"""Pricing engine with real per-channel fee models.

All math is Decimal end-to-end. Fee models reflect what the platforms
actually charge (transaction % + payment processing % + fixed fees), and
`simulate_worst_case` + `profitability_risk_flags` make margin risk explicit
before a product is listed.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional


_TWO = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(_TWO, rounding=ROUND_HALF_UP)


def to_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
    """Convert any numeric input to Decimal without float contamination."""
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Per-channel fee models (kept current as of 2026 fee schedules)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ChannelFeeModel:
    """What a channel actually takes from a sale.

    percent_fee:    marketplace transaction fee, as a fraction of revenue
    payment_pct:    payment-processing percentage (platform's processor,
                    or Stripe for our own website)
    payment_fixed:  fixed payment-processing fee per order
    listing_fee:    fixed fee per listing/sale (e.g. Etsy $0.20)
    """
    name: str
    percent_fee: Decimal
    payment_pct: Decimal
    payment_fixed: Decimal
    listing_fee: Decimal = Decimal("0")

    def total_fees(self, revenue: Decimal) -> Decimal:
        revenue = to_decimal(revenue)
        return _round(
            revenue * self.percent_fee
            + revenue * self.payment_pct
            + self.payment_fixed
            + self.listing_fee
        )

    @property
    def total_pct(self) -> Decimal:
        return self.percent_fee + self.payment_pct

    @property
    def total_fixed(self) -> Decimal:
        return self.payment_fixed + self.listing_fee


CHANNEL_FEES: dict[str, ChannelFeeModel] = {
    # Our own site: no platform fee; Stripe 2.9% + $0.30.
    "website": ChannelFeeModel("website", Decimal("0"), Decimal("0.029"), Decimal("0.30")),
    # Etsy: 6.5% transaction + Etsy Payments 3% + $0.25 + $0.20 listing fee.
    "etsy": ChannelFeeModel("etsy", Decimal("0.065"), Decimal("0.03"), Decimal("0.25"), Decimal("0.20")),
    # eBay: ~13.25% final value fee (most categories) + $0.30 per order.
    "ebay": ChannelFeeModel("ebay", Decimal("0.1325"), Decimal("0"), Decimal("0.30")),
    # Facebook/Meta checkout: 5% or $0.40 minimum — modeled as 5%.
    "facebook": ChannelFeeModel("facebook", Decimal("0.05"), Decimal("0"), Decimal("0")),
    # TikTok Shop: ~6% marketplace commission (post-intro pricing).
    "tiktok_shop": ChannelFeeModel("tiktok_shop", Decimal("0.06"), Decimal("0"), Decimal("0")),
}

_DEFAULT_FEE_MODEL = ChannelFeeModel("unknown", Decimal("0.10"), Decimal("0"), Decimal("0.30"))


def get_fee_model(channel: str) -> ChannelFeeModel:
    return CHANNEL_FEES.get(channel, _DEFAULT_FEE_MODEL)


# ---------------------------------------------------------------------------
# Price calculation
# ---------------------------------------------------------------------------

def calculate_website_price(
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    markup_multiplier: Decimal = Decimal("2.8"),
    min_margin_pct: Decimal = Decimal("40"),
) -> Decimal:
    total_cost = to_decimal(supplier_cost) + to_decimal(shipping_cost)
    price = _round(total_cost * markup_multiplier)
    min_price = _round(total_cost / (1 - min_margin_pct / 100))
    return max(price, min_price)


def calculate_marketplace_price(
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    platform: str = "etsy",
    markup_multiplier: Decimal = Decimal("3.2"),
) -> Decimal:
    """Gross up the target price so that, after the platform's percentage AND
    fixed fees, we still clear cost * multiplier."""
    fees = get_fee_model(platform)
    total_cost = to_decimal(supplier_cost) + to_decimal(shipping_cost)
    base_price = total_cost * to_decimal(markup_multiplier)
    # price = (base + fixed) / (1 - pct)  →  net after fees == base
    price = (base_price + fees.total_fixed) / (Decimal("1") - fees.total_pct)
    return _round(price)


def calculate_margin(
    sell_price: Decimal,
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    platform_fee_rate: Decimal = Decimal("0"),
    channel: Optional[str] = None,
) -> dict:
    """Margin breakdown. Pass `channel` to use the full fee model (percentage
    + fixed); `platform_fee_rate` is kept for backwards compatibility."""
    sell_price = to_decimal(sell_price)
    total_cost = to_decimal(supplier_cost) + to_decimal(shipping_cost)
    if channel:
        platform_fee = get_fee_model(channel).total_fees(sell_price)
    else:
        platform_fee = _round(sell_price * to_decimal(platform_fee_rate))
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
    price = _round(to_decimal(base_price) * to_decimal(multiplier) + to_decimal(fixed_addition))
    if min_price:
        price = max(price, min_price)
    if max_price:
        price = min(price, max_price)
    return price


def bulk_price_products(
    products: list[dict],
    website_multiplier: Decimal = Decimal("2.8"),
    marketplace_multiplier: Decimal = Decimal("3.2"),
    marketplace_platform: str = "etsy",
) -> list[dict]:
    result = []
    for p in products:
        cost = to_decimal(p.get("supplier_cost", 0))
        shipping = to_decimal(p.get("shipping_cost", 0))
        result.append({
            **p,
            "website_price": calculate_website_price(cost, shipping, website_multiplier),
            "marketplace_price": calculate_marketplace_price(
                cost, shipping, platform=marketplace_platform,
                markup_multiplier=marketplace_multiplier,
            ),
        })
    return result


# ---------------------------------------------------------------------------
# Worst-case margin simulation + risk flags
# ---------------------------------------------------------------------------

# Stress assumptions for the worst-case scenario.
_SHIPPING_VARIANCE = Decimal("0.35")   # outbound shipping comes in 35% over estimate
_SUPPLIER_COST_DRIFT = Decimal("0.10")  # supplier raises cost 10% before we reprice
_THIN_MARGIN_PCT = Decimal("15")        # below this, one surprise wipes the profit


def simulate_worst_case(
    sell_price: Decimal,
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    channel: str = "website",
) -> dict:
    """Margin under pessimistic-but-realistic assumptions.

    Stress factors: shipping +35%, supplier cost +10%, full channel fees.
    If the worst case is negative, this product can lose money on a bad day.
    """
    sell_price = to_decimal(sell_price)
    supplier_cost = to_decimal(supplier_cost)
    shipping_cost = to_decimal(shipping_cost)
    fees = get_fee_model(channel)

    expected = calculate_margin(sell_price, supplier_cost, shipping_cost, channel=channel)

    stressed_supplier = _round(supplier_cost * (1 + _SUPPLIER_COST_DRIFT))
    stressed_shipping = _round(shipping_cost * (1 + _SHIPPING_VARIANCE))
    worst = calculate_margin(sell_price, stressed_supplier, stressed_shipping, channel=channel)

    return {
        "channel": channel,
        "sell_price": sell_price,
        "expected_profit": expected["profit"],
        "expected_margin_pct": expected["margin_pct"],
        "worst_case_profit": worst["profit"],
        "worst_case_margin_pct": worst["margin_pct"],
        "fee_total": expected["platform_fee"],
        "assumptions": {
            "shipping_variance_pct": str(_SHIPPING_VARIANCE * 100),
            "supplier_cost_drift_pct": str(_SUPPLIER_COST_DRIFT * 100),
        },
    }


def profitability_risk_flags(
    sell_price: Decimal,
    supplier_cost: Decimal,
    shipping_cost: Decimal = Decimal("0"),
    channel: str = "website",
    supplier_cost_change_pct: Decimal = Decimal("0"),
) -> list[dict]:
    """Risk flags shown in the admin before/while a product is listed.

    Flags: negative_margin_after_fees, worst_case_negative, thin_margin,
    shipping_variance_risk, supplier_volatility.
    """
    flags: list[dict] = []
    sim = simulate_worst_case(sell_price, supplier_cost, shipping_cost, channel)

    if sim["expected_profit"] <= 0:
        flags.append({
            "flag": "negative_margin_after_fees",
            "severity": "critical",
            "detail": f"Selling at {sell_price} on {channel} loses "
                      f"{abs(sim['expected_profit'])} per unit after fees.",
        })
    elif sim["worst_case_profit"] <= 0:
        flags.append({
            "flag": "worst_case_negative",
            "severity": "error",
            "detail": "Profitable on paper, but a shipping overrun or supplier "
                      "cost bump makes this order lose money "
                      f"(worst case {sim['worst_case_profit']}).",
        })
    elif sim["expected_margin_pct"] < _THIN_MARGIN_PCT:
        flags.append({
            "flag": "thin_margin",
            "severity": "warning",
            "detail": f"Expected margin {sim['expected_margin_pct']}% is below "
                      f"the {_THIN_MARGIN_PCT}% safety threshold.",
        })

    shipping = to_decimal(shipping_cost)
    if sim["expected_profit"] > 0 and shipping > 0 and (shipping * _SHIPPING_VARIANCE) > sim["expected_profit"] * Decimal("0.5"):
        flags.append({
            "flag": "shipping_variance_risk",
            "severity": "warning",
            "detail": "A 35% shipping overrun consumes more than half the expected profit.",
        })

    if to_decimal(supplier_cost_change_pct) >= Decimal("5"):
        flags.append({
            "flag": "supplier_volatility",
            "severity": "warning",
            "detail": f"Supplier cost moved {supplier_cost_change_pct}% recently — "
                      "price may be stale.",
        })

    return flags
