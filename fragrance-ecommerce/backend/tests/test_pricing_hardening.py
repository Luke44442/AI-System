"""Fee models, worst-case simulation, and risk flags — money math guards."""
from decimal import Decimal

from app.services.pricing_engine import (
    CHANNEL_FEES, get_fee_model, to_decimal,
    calculate_marketplace_price, calculate_margin,
    bulk_price_products, simulate_worst_case, profitability_risk_flags,
)


def test_fee_model_etsy_includes_fixed_fees():
    fees = get_fee_model("etsy").total_fees(Decimal("100"))
    # 6.5% + 3% + $0.25 + $0.20 = $9.95
    assert fees == Decimal("9.95")


def test_fee_model_unknown_channel_is_conservative():
    fees = get_fee_model("nonexistent")
    assert fees.percent_fee >= Decimal("0.10")


def test_marketplace_price_grosses_up_fixed_fees():
    price = calculate_marketplace_price(Decimal("10"), Decimal("0"), platform="etsy",
                                        markup_multiplier=Decimal("3"))
    # Net revenue after full Etsy fees must cover cost * multiplier.
    fees = get_fee_model("etsy")
    net = price - fees.total_fees(price)
    assert net >= Decimal("30") - Decimal("0.05")  # rounding tolerance


def test_margin_with_channel_uses_full_fee_model():
    m = calculate_margin(Decimal("100"), Decimal("30"), Decimal("8"), channel="etsy")
    assert m["platform_fee"] == Decimal("9.95")
    assert m["profit"] == Decimal("100") - Decimal("9.95") - Decimal("38")


def test_bulk_price_products_regression():
    # This used to raise TypeError (multiplier= kwarg didn't exist).
    out = bulk_price_products([{"supplier_cost": "10", "shipping_cost": "2"}])
    assert out[0]["website_price"] > Decimal("0")
    assert out[0]["marketplace_price"] > out[0]["website_price"]


def test_to_decimal_never_floats():
    assert to_decimal(0.1) == Decimal("0.1")
    assert to_decimal("bad", Decimal("1")) == Decimal("1")
    assert to_decimal(None) == Decimal("0")


# ---------------------------------------------------------------------------
# Worst-case simulation + risk flags
# ---------------------------------------------------------------------------

def test_worst_case_is_worse_than_expected():
    sim = simulate_worst_case(Decimal("100"), Decimal("40"), Decimal("10"), "etsy")
    assert sim["worst_case_profit"] < sim["expected_profit"]
    assert sim["worst_case_margin_pct"] < sim["expected_margin_pct"]


def test_negative_margin_flagged_critical():
    # Selling at 30 with cost 40 — guaranteed loss.
    flags = profitability_risk_flags(Decimal("30"), Decimal("40"), Decimal("0"), "etsy")
    assert any(f["flag"] == "negative_margin_after_fees" and f["severity"] == "critical"
               for f in flags)


def test_worst_case_negative_flagged():
    # Profitable on paper but barely: cost 80 + shipping 10 vs price 100 on
    # website (~6.7 profit). Worst case (+10% cost, +35% shipping) goes negative.
    flags = profitability_risk_flags(Decimal("100"), Decimal("80"), Decimal("10"), "website")
    assert any(f["flag"] in ("worst_case_negative", "negative_margin_after_fees")
               for f in flags)


def test_healthy_product_has_no_flags():
    flags = profitability_risk_flags(Decimal("100"), Decimal("20"), Decimal("5"), "website")
    assert flags == []


def test_supplier_volatility_flag():
    flags = profitability_risk_flags(
        Decimal("100"), Decimal("20"), Decimal("5"), "website",
        supplier_cost_change_pct=Decimal("8"),
    )
    assert any(f["flag"] == "supplier_volatility" for f in flags)
