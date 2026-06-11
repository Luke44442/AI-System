from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


from app.services.pricing_engine import get_fee_model

_TWO = Decimal("0.01")
_FOUR = Decimal("0.0001")

# Stripe fee constants (our own website's payment processor)
_STRIPE_RATE = Decimal("0.029")          # 2.9%
_STRIPE_FIXED = Decimal("0.30")          # $0.30 per transaction

# Alert thresholds
_MIN_MARGIN_PCT = Decimal("30")          # alert when margin drops below 30%
_COMPETITOR_CHEAPER_THRESHOLD = Decimal("0.10")  # alert when competitor is >10% cheaper
_COST_INCREASE_THRESHOLD = Decimal("0.05")       # alert when cost rose >5%


def _round2(value: Decimal) -> Decimal:
    return value.quantize(_TWO, rounding=ROUND_HALF_UP)


def _round4(value: Decimal) -> Decimal:
    return value.quantize(_FOUR, rounding=ROUND_HALF_UP)


def _to_decimal(value: object) -> Decimal:
    """Convert any numeric type to Decimal safely."""
    return Decimal(str(value))


# ---------------------------------------------------------------------------
# Core profitability calculation
# ---------------------------------------------------------------------------

def calculate_order_profitability(
    order_total: Decimal,
    supplier_cost: Decimal,
    shipping_cost: Decimal,
    channel: str = "website",
) -> dict:
    """Calculate full profitability breakdown for a single order.

    Args:
        order_total:   Total revenue collected from the customer.
        supplier_cost: Landed cost of goods from supplier.
        shipping_cost: Outbound shipping cost paid by us.
        channel:       Sales channel — 'website', 'etsy', 'ebay', 'facebook'.

    Returns a dict with all cost/profit/margin fields suitable for persisting
    into an OrderProfitability row.
    """
    revenue = _round2(order_total)
    supplier_cost = _round2(supplier_cost)
    shipping_cost = _round2(shipping_cost)

    # Marketplace orders are paid through the platform's own processor (Etsy
    # Payments, eBay Managed Payments, ...) — those costs live in the channel
    # fee model. Stripe only applies to orders on our own website.
    if channel == "website":
        platform_fee = Decimal("0.00")
        stripe_fee = _round2(revenue * _STRIPE_RATE + _STRIPE_FIXED)
    else:
        platform_fee = get_fee_model(channel).total_fees(revenue)
        stripe_fee = Decimal("0.00")

    other_fees = Decimal("0.00")

    gross_profit = _round2(revenue - supplier_cost - shipping_cost)
    net_profit = _round2(
        revenue - supplier_cost - shipping_cost - platform_fee - stripe_fee - other_fees
    )
    margin_pct = (
        _round4(net_profit / revenue * Decimal("100"))
        if revenue > Decimal("0")
        else Decimal("0")
    )

    return {
        "revenue": revenue,
        "supplier_cost": supplier_cost,
        "shipping_cost": shipping_cost,
        "platform_fee": platform_fee,
        "stripe_fee": stripe_fee,
        "other_fees": other_fees,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "margin_pct": margin_pct,
        "channel": channel,
    }


# ---------------------------------------------------------------------------
# Price optimisation suggestion
# ---------------------------------------------------------------------------

def suggest_price_optimization(product: dict) -> dict:
    """Suggest a price adjustment based on cost, current price, and performance.

    Args:
        product: Dict with keys:
            - supplier_cost   (Decimal | float | str)
            - website_price   (Decimal | float | str)
            - order_count     (int)   — historical order volume
            - conversion_rate (float) — as a percentage, e.g. 2.5 for 2.5%

    Returns:
        suggested_price (Decimal), reasoning (str), expected_impact (str),
        action ('increase' | 'decrease' | 'maintain')
    """
    supplier_cost = _to_decimal(product.get("supplier_cost", 0))
    website_price = _to_decimal(product.get("website_price", 0))
    order_count = int(product.get("order_count", 0))
    conversion_rate = float(product.get("conversion_rate", 0))

    if website_price <= Decimal("0"):
        return {
            "suggested_price": website_price,
            "reasoning": "Current price is zero or invalid — set a valid price first.",
            "expected_impact": "N/A",
            "action": "maintain",
        }

    current_margin = (
        (website_price - supplier_cost) / website_price * Decimal("100")
        if website_price > Decimal("0")
        else Decimal("0")
    )

    # --- Decision logic ---

    # Low margin AND healthy conversion → raise price slightly
    if current_margin < Decimal("35") and conversion_rate >= 2.0:
        factor = Decimal("1.10")
        suggested_price = _round2(website_price * factor)
        action = "increase"
        reasoning = (
            f"Current margin is {_round2(current_margin)}% which is below the 35% target, "
            f"but conversion rate ({conversion_rate:.1f}%) indicates strong demand. "
            "A modest 10% price increase should improve profitability without hurting volume significantly."
        )
        expected_impact = "Estimated +10% revenue per unit; margin improvement of ~8-10 pp."

    # Very high margin AND poor conversion → lower price to drive volume
    elif current_margin > Decimal("60") and conversion_rate < 1.0 and order_count < 10:
        factor = Decimal("0.90")
        suggested_price = _round2(website_price * factor)
        action = "decrease"
        reasoning = (
            f"Margin is {_round2(current_margin)}% which is well above target, "
            f"but low conversion rate ({conversion_rate:.1f}%) and order count ({order_count}) "
            "suggest the price may be deterring buyers. A 10% reduction could unlock volume growth."
        )
        expected_impact = "Estimated conversion improvement of 0.5-1.5 pp; higher total revenue at scale."

    # Margin critically low → recommend increase regardless of conversion
    elif current_margin < Decimal("20"):
        min_viable = _round2(supplier_cost / (Decimal("1") - Decimal("0.35")))
        suggested_price = max(_round2(website_price * Decimal("1.15")), min_viable)
        action = "increase"
        reasoning = (
            f"Margin of {_round2(current_margin)}% is critically below the 20% floor. "
            "Price must increase to cover costs and provide a sustainable margin."
        )
        expected_impact = "Brings minimum margin to ~35%; some conversion loss expected."

    else:
        # Price looks fine — maintain
        suggested_price = website_price
        action = "maintain"
        reasoning = (
            f"Current margin ({_round2(current_margin)}%) and conversion rate "
            f"({conversion_rate:.1f}%) are within healthy ranges. No adjustment recommended."
        )
        expected_impact = "No material change expected."

    return {
        "suggested_price": suggested_price,
        "reasoning": reasoning,
        "expected_impact": expected_impact,
        "action": action,
    }


# ---------------------------------------------------------------------------
# Pricing alert detection
# ---------------------------------------------------------------------------

def detect_pricing_alerts(product: dict, competitor_prices: list) -> list:
    """Analyse a product and its competitor landscape and return any active alerts.

    Args:
        product: Dict with keys:
            - id              (str | UUID)
            - supplier_cost   (Decimal | float | str)
            - website_price   (Decimal | float | str)
            - previous_cost   (Decimal | float | str, optional) — last known cost
        competitor_prices: List of dicts, each with:
            - competitor_name (str)
            - competitor_price (Decimal | float | str)

    Returns a list of PricingAlert-shaped dicts (no DB model dependency).
    """
    alerts: list[dict] = []

    product_id = product.get("id", str(uuid.uuid4()))
    supplier_cost = _to_decimal(product.get("supplier_cost", 0))
    website_price = _to_decimal(product.get("website_price", 0))
    previous_cost = _to_decimal(product.get("previous_cost", 0))

    if website_price <= Decimal("0"):
        return alerts

    # -----------------------------------------------------------------------
    # Alert 1: margin below 30%
    # -----------------------------------------------------------------------
    current_margin = _round4(
        (website_price - supplier_cost) / website_price * Decimal("100")
    )
    if current_margin < _MIN_MARGIN_PCT:
        alerts.append(
            _build_alert(
                product_id=product_id,
                alert_type="low_margin",
                message=(
                    f"Net margin is {_round2(current_margin)}%, below the 30% minimum threshold. "
                    "Consider raising the price or renegotiating supplier cost."
                ),
                current_value=current_margin,
                threshold_value=_MIN_MARGIN_PCT,
            )
        )

    # -----------------------------------------------------------------------
    # Alert 2: competitor cheaper by more than 10%
    # -----------------------------------------------------------------------
    for comp in competitor_prices:
        comp_price = _to_decimal(comp.get("competitor_price", 0))
        comp_name = str(comp.get("competitor_name", "Unknown"))
        if comp_price <= Decimal("0"):
            continue

        price_diff_pct = _round4(
            (website_price - comp_price) / comp_price * Decimal("100")
        )
        # We are more expensive — positive price_diff_pct means we're pricier
        if price_diff_pct > _COMPETITOR_CHEAPER_THRESHOLD * Decimal("100"):
            alerts.append(
                _build_alert(
                    product_id=product_id,
                    alert_type="competitor_cheaper",
                    message=(
                        f"{comp_name} is selling at ${_round2(comp_price)}, "
                        f"which is {_round2(price_diff_pct)}% cheaper than our price of "
                        f"${_round2(website_price)}. Review pricing strategy."
                    ),
                    current_value=price_diff_pct,
                    threshold_value=_COMPETITOR_CHEAPER_THRESHOLD * Decimal("100"),
                )
            )

    # -----------------------------------------------------------------------
    # Alert 3: supplier cost increased by more than 5%
    # -----------------------------------------------------------------------
    if previous_cost > Decimal("0") and supplier_cost > previous_cost:
        cost_increase_pct = _round4(
            (supplier_cost - previous_cost) / previous_cost * Decimal("100")
        )
        if cost_increase_pct > _COST_INCREASE_THRESHOLD * Decimal("100"):
            alerts.append(
                _build_alert(
                    product_id=product_id,
                    alert_type="cost_increase",
                    message=(
                        f"Supplier cost increased by {_round2(cost_increase_pct)}% "
                        f"(from ${_round2(previous_cost)} to ${_round2(supplier_cost)}). "
                        "Review pricing to maintain target margins."
                    ),
                    current_value=cost_increase_pct,
                    threshold_value=_COST_INCREASE_THRESHOLD * Decimal("100"),
                )
            )

    return alerts


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_alert(
    product_id: object,
    alert_type: str,
    message: str,
    current_value: Decimal,
    threshold_value: Decimal,
) -> dict:
    """Build a PricingAlert-shaped dict ready for DB insertion."""
    return {
        "id": str(uuid.uuid4()),
        "product_id": str(product_id),
        "alert_type": alert_type,
        "message": message,
        "current_value": current_value,
        "threshold_value": threshold_value,
        "is_resolved": False,
        "resolved_at": None,
    }
