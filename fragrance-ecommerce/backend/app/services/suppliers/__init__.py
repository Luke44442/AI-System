"""Supplier fulfillment adapters.

Distinct from `automation/suppliers` (catalog scraping): these adapters PLACE
ORDERS with suppliers. Each adapter implements the same surface so the
orchestrator can drive any supplier uniformly:

    place_order(request)            -> SupplierOrderResult
    get_order_status(external_id)   -> SupplierOrderResult

Adapter selection is by `Supplier.type`:
    "cj_dropshipping" / "cj" -> CJDropshippingAdapter (real API)
    "mock"                   -> MockSupplierAdapter   (dev/testing)
    anything else            -> None → orchestrator routes to the manual queue
"""
from __future__ import annotations
from typing import Optional

from app.services.suppliers.base import (  # noqa: F401
    SupplierFulfillmentAdapter,
    SupplierOrderRequest,
    SupplierOrderItem,
    SupplierOrderResult,
    SupplierOrderStatus,
    SupplierAPIError,
)
from app.services.suppliers.cj import CJDropshippingAdapter
from app.services.suppliers.mock import MockSupplierAdapter

_ADAPTERS = {
    "cj_dropshipping": CJDropshippingAdapter,
    "cj": CJDropshippingAdapter,
    "mock": MockSupplierAdapter,
}


def get_fulfillment_adapter(supplier_type: Optional[str], credentials: Optional[dict] = None) -> Optional[SupplierFulfillmentAdapter]:
    """Return a configured adapter for this supplier type, or None for manual handling."""
    cls = _ADAPTERS.get((supplier_type or "").lower())
    if cls is None:
        return None
    adapter = cls(credentials or {})
    return adapter if adapter.is_configured() else None
