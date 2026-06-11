"""Supplier fulfillment adapters + orchestrator plumbing — no network, no DB."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.suppliers import get_fulfillment_adapter
from app.services.suppliers.base import (
    SupplierAPIError, SupplierOrderItem, SupplierOrderRequest, SupplierOrderStatus,
)
from app.services.suppliers.mock import MockSupplierAdapter
from app.services.suppliers.cj import CJDropshippingAdapter
from app.services.supplier_orchestrator import _normalize_address


def sample_request() -> SupplierOrderRequest:
    return SupplierOrderRequest(
        order_number="SCN-123456",
        items=[SupplierOrderItem(supplier_sku="CJ-SKU-1", quantity=2, unit_cost=Decimal("12.50"))],
        shipping_address={
            "first_name": "Ada", "last_name": "Lovelace",
            "line1": "1 Analytical Way", "city": "London",
            "postal_code": "SW1", "country": "GB",
        },
    )


# ---------------------------------------------------------------------------
# Adapter registry routing
# ---------------------------------------------------------------------------

def test_unknown_supplier_type_routes_to_manual():
    assert get_fulfillment_adapter("alibaba_manual") is None
    assert get_fulfillment_adapter(None) is None


def test_mock_adapter_always_available():
    adapter = get_fulfillment_adapter("mock")
    assert isinstance(adapter, MockSupplierAdapter)


def test_cj_unconfigured_returns_none(monkeypatch):
    monkeypatch.setattr("app.services.suppliers.cj.settings.CJ_EMAIL", None)
    monkeypatch.setattr("app.services.suppliers.cj.settings.CJ_API_KEY", None)
    assert get_fulfillment_adapter("cj_dropshipping") is None


def test_cj_configured_via_supplier_credentials(monkeypatch):
    monkeypatch.setattr("app.services.suppliers.cj.settings.CJ_EMAIL", None)
    monkeypatch.setattr("app.services.suppliers.cj.settings.CJ_API_KEY", None)
    adapter = get_fulfillment_adapter("cj", {"email": "a@b.com", "api_key": "k"})
    assert isinstance(adapter, CJDropshippingAdapter)
    assert adapter.is_configured()


# ---------------------------------------------------------------------------
# Mock adapter terminal behaviors (drives orchestrator state machine)
# ---------------------------------------------------------------------------

def test_mock_places_order():
    result = MockSupplierAdapter({}).place_order(sample_request())
    assert result.status == SupplierOrderStatus.PLACED
    assert result.external_order_id.startswith("MOCK-")


def test_mock_nonretryable_failure():
    with pytest.raises(SupplierAPIError) as exc_info:
        MockSupplierAdapter({"mode": "fail"}).place_order(sample_request())
    assert exc_info.value.retryable is False


def test_mock_retryable_failure():
    with pytest.raises(SupplierAPIError) as exc_info:
        MockSupplierAdapter({"mode": "fail_retryable"}).place_order(sample_request())
    assert exc_info.value.retryable is True


def test_mock_tracking_returns_shipped():
    result = MockSupplierAdapter({}).get_order_status("MOCK-ABCDEFGH")
    assert result.status == SupplierOrderStatus.SHIPPED
    assert result.tracking_number


# ---------------------------------------------------------------------------
# Address normalization (internal address1/address2 → adapter line1/line2)
# ---------------------------------------------------------------------------

def test_normalize_address_maps_internal_shape():
    addr = _normalize_address({
        "first_name": "Ada", "last_name": "Lovelace",
        "address1": "1 Analytical Way", "address2": "Suite 2",
        "city": "London", "postal_code": "SW1", "country": "GB",
    })
    assert addr["line1"] == "1 Analytical Way"
    assert addr["line2"] == "Suite 2"
    assert addr["country"] == "GB"


def test_normalize_address_handles_missing():
    addr = _normalize_address(None)
    assert addr["line1"] == ""
    assert addr["country"] == "US"
