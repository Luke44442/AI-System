"""Marketplace adapter unit tests — no network, no database.

Each adapter must:
  1. Return SKIPPED (not raise) when credentials are absent.
  2. Call the right underlying API method when credentials are present.

The conftest autouse fixture clears all marketplace env vars before each test.
We patch `settings` attributes directly since the Settings singleton is
constructed at import time and env-var mutations don't reach it.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.marketplaces.base import ProductPayload, SyncStatus
from app.services.marketplaces.etsy import EtsyAdapter
from app.services.marketplaces.ebay import EbayAdapter
from app.services.marketplaces.tiktok import TikTokShopAdapter as TikTokAdapter
from app.services.marketplaces.pinterest import PinterestAdapter
from app.services.marketplaces.google import GoogleMerchantAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sample_product(**overrides) -> ProductPayload:
    base = dict(
        id="abc123",
        sku="TF-OUD-100",
        title="Tom Ford Oud Wood 100ml",
        description="Smoky oriental woody fragrance.",
        price=Decimal("310.00"),
        quantity=5,
        brand="Tom Ford",
        category="Fragrances",
        product_type="fragrance",
        tags=["tom ford", "oud wood"],
        images=["https://cdn.example.com/oud.jpg"],
    )
    base.update(overrides)
    return ProductPayload(**base)


_SETTINGS_MODULE = "app.config.settings"


# ---------------------------------------------------------------------------
# is_configured — must return False when credentials are None (default)
# ---------------------------------------------------------------------------

def test_etsy_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_API_KEY", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_ACCESS_TOKEN", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_SHOP_ID", None)
    assert EtsyAdapter().is_configured() is False


def test_ebay_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_APP_ID", None)
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_CERT_ID", None)
    assert EbayAdapter().is_configured() is False


def test_tiktok_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.tiktok.settings.TIKTOK_SHOP_APP_KEY", None)
    monkeypatch.setattr("app.services.marketplaces.tiktok.settings.TIKTOK_SHOP_ACCESS_TOKEN", None)
    assert TikTokAdapter().is_configured() is False


def test_pinterest_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.pinterest.settings.PINTEREST_ACCESS_TOKEN", None)
    assert PinterestAdapter().is_configured() is False


def test_google_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.google.settings.GOOGLE_MERCHANT_ID", None)
    monkeypatch.setattr("app.services.marketplaces.google.settings.GOOGLE_MERCHANT_CREDENTIALS_JSON", None)
    assert GoogleMerchantAdapter().is_configured() is False


# ---------------------------------------------------------------------------
# create_listing → SKIPPED when unconfigured
# ---------------------------------------------------------------------------

def test_etsy_create_skipped_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_API_KEY", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_ACCESS_TOKEN", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_SHOP_ID", None)
    result = EtsyAdapter().create_listing(sample_product())
    assert result.status == SyncStatus.SKIPPED
    assert result.ok is True


def test_ebay_create_skipped_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_APP_ID", None)
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_CERT_ID", None)
    result = EbayAdapter().create_listing(sample_product())
    assert result.status == SyncStatus.SKIPPED


def test_tiktok_create_skipped_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.tiktok.settings.TIKTOK_SHOP_APP_KEY", None)
    monkeypatch.setattr("app.services.marketplaces.tiktok.settings.TIKTOK_SHOP_ACCESS_TOKEN", None)
    result = TikTokAdapter().create_listing(sample_product())
    assert result.status == SyncStatus.SKIPPED


def test_pinterest_create_skipped_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.pinterest.settings.PINTEREST_ACCESS_TOKEN", None)
    result = PinterestAdapter().create_listing(sample_product())
    assert result.status == SyncStatus.SKIPPED


def test_google_create_skipped_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.google.settings.GOOGLE_MERCHANT_ID", None)
    monkeypatch.setattr("app.services.marketplaces.google.settings.GOOGLE_MERCHANT_CREDENTIALS_JSON", None)
    result = GoogleMerchantAdapter().create_listing(sample_product())
    assert result.status == SyncStatus.SKIPPED


# ---------------------------------------------------------------------------
# update_listing / delete_listing → SKIPPED when unconfigured
# ---------------------------------------------------------------------------

def test_etsy_update_and_delete_skipped(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_API_KEY", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_ACCESS_TOKEN", None)
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_SHOP_ID", None)
    adapter = EtsyAdapter()
    assert adapter.update_listing("123", sample_product()).status == SyncStatus.SKIPPED
    assert adapter.delete_listing("123").status == SyncStatus.SKIPPED


def test_ebay_update_and_delete_skipped(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_APP_ID", None)
    monkeypatch.setattr("app.services.marketplaces.ebay.settings.EBAY_CERT_ID", None)
    adapter = EbayAdapter()
    assert adapter.update_listing("123", sample_product()).status == SyncStatus.SKIPPED
    assert adapter.delete_listing("123").status == SyncStatus.SKIPPED


# ---------------------------------------------------------------------------
# SyncResult.ok semantics
# ---------------------------------------------------------------------------

def test_sync_result_ok_for_success_and_skipped():
    from app.services.marketplaces.base import SyncResult

    ok_success = SyncResult("etsy", SyncStatus.SUCCESS)
    ok_skipped = SyncResult("etsy", SyncStatus.SKIPPED)
    not_ok = SyncResult("etsy", SyncStatus.FAILED)
    not_supported = SyncResult("etsy", SyncStatus.NOT_SUPPORTED)

    assert ok_success.ok is True
    assert ok_skipped.ok is True
    assert not_ok.ok is False
    assert not_supported.ok is False


# ---------------------------------------------------------------------------
# Configured adapter actually calls the underlying client (mock the client)
# ---------------------------------------------------------------------------

def test_etsy_configured_calls_client(monkeypatch):
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_API_KEY", "key")
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_ACCESS_TOKEN", "token")
    monkeypatch.setattr("app.services.marketplaces.etsy.settings.ETSY_SHOP_ID", "shop123")

    fake_client = MagicMock()
    fake_client.create_listing.return_value = {"listing_id": 42}
    fake_client.upload_listing_image.return_value = {}

    adapter = EtsyAdapter()
    with patch.object(adapter, "_client", return_value=fake_client):
        result = adapter.create_listing(sample_product())

    fake_client.create_listing.assert_called_once()
    assert result.status == SyncStatus.SUCCESS
    assert result.listing_id == "42"
