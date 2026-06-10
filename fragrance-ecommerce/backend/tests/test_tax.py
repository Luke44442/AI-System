"""Tax calculation — money-critical, must stay correct."""
from decimal import Decimal

from app.services.tax import calculate_tax, estimate_tax_rate


def test_no_address_means_no_tax():
    assert calculate_tax(Decimal("100"), None) == Decimal("0.00")


def test_no_sales_tax_states():
    for state in ("OR", "MT", "NH", "DE"):
        assert calculate_tax(Decimal("200"), {"country": "US", "state": state}) == Decimal("0.00")


def test_california_rate_applied():
    rate = estimate_tax_rate({"country": "US", "state": "CA"})
    assert rate == Decimal("0.0882")
    tax = calculate_tax(Decimal("100.00"), {"country": "US", "state": "CA"})
    assert tax == Decimal("8.82")


def test_international_is_untaxed():
    assert calculate_tax(Decimal("500"), {"country": "GB", "state": "London"}) == Decimal("0.00")


def test_rounding_to_cents():
    # 7.35% of 49.99 = 3.674... -> 3.67
    tax = calculate_tax(Decimal("49.99"), {"country": "US", "state": "GA"})
    assert tax == Decimal("3.67")


def test_zero_amount_no_tax():
    assert calculate_tax(Decimal("0"), {"country": "US", "state": "CA"}) == Decimal("0.00")


def test_unknown_state_defaults_zero():
    assert calculate_tax(Decimal("100"), {"country": "US", "state": "ZZ"}) == Decimal("0.00")
