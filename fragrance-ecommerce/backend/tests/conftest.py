"""Shared test fixtures.

These tests are split into two tiers:
  * pure-logic tests (tax, pricing, profitability, marketplace adapters) run with
    no database or network — they protect the money-critical math and the
    marketplace sync behavior.
  * API/integration tests are marked `@pytest.mark.integration` and require a
    test database (set TEST_DATABASE_URL); they're skipped automatically when it
    isn't configured.
"""
import os
import types
from decimal import Decimal

import pytest


def make_product(**overrides):
    """A lightweight stand-in for the Product ORM object for unit tests."""
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        sku="TF-OUDWOOD-100-U",
        name="Oud Wood",
        slug="tom-ford-oud-wood",
        description="Smoky oud and sandalwood.",
        seo_description="Tom Ford Oud Wood EDP",
        website_price=Decimal("310.00"),
        marketplace_price=Decimal("355.00"),
        inventory_quantity=20,
        fragrance_family="Oriental Woody",
        style_category=None,
        product_type="fragrance",
        concentration="eau de parfum",
        gender="unisex",
        tags=["tom ford", "oud"],
        images=[{"url": "https://img/oud.jpg", "is_primary": True}],
        attributes={"concentration": "Eau de Parfum"},
        brand=types.SimpleNamespace(name="Tom Ford"),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


@pytest.fixture
def product():
    return make_product()


@pytest.fixture(autouse=True)
def _clear_marketplace_env(monkeypatch):
    """Ensure marketplace adapters start unconfigured unless a test sets creds."""
    for var in ["ETSY_API_KEY", "ETSY_ACCESS_TOKEN", "ETSY_SHOP_ID",
                "EBAY_APP_ID", "EBAY_CERT_ID",
                "TIKTOK_SHOP_APP_KEY", "TIKTOK_SHOP_ACCESS_TOKEN",
                "PINTEREST_ACCESS_TOKEN",
                "GOOGLE_MERCHANT_ID", "GOOGLE_MERCHANT_CREDENTIALS_JSON"]:
        monkeypatch.delenv(var, raising=False)
    yield
