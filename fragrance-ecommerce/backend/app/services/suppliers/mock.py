"""Mock supplier adapter for development and end-to-end testing.

Behavior is driven by the supplier's `credentials` JSON:
    {"mode": "success"}        — always places (default)
    {"mode": "fail"}           — non-retryable business failure
    {"mode": "fail_retryable"} — transient failure (exercises the retry loop)
"""
from __future__ import annotations
import uuid

from app.services.suppliers.base import (
    SupplierFulfillmentAdapter,
    SupplierOrderRequest,
    SupplierOrderResult,
    SupplierOrderStatus,
    SupplierAPIError,
)


class MockSupplierAdapter(SupplierFulfillmentAdapter):
    name = "mock"

    def is_configured(self) -> bool:
        return True

    def place_order(self, request: SupplierOrderRequest) -> SupplierOrderResult:
        mode = self.credentials.get("mode", "success")
        if mode == "fail":
            raise SupplierAPIError("mock: business rejection (e.g. SKU not found)", retryable=False)
        if mode == "fail_retryable":
            raise SupplierAPIError("mock: transient supplier outage", retryable=True)
        return SupplierOrderResult(
            status=SupplierOrderStatus.PLACED,
            external_order_id=f"MOCK-{uuid.uuid4().hex[:10].upper()}",
            external_status="CREATED",
            message="mock order placed",
        )

    def get_order_status(self, external_order_id: str) -> SupplierOrderResult:
        return SupplierOrderResult(
            status=SupplierOrderStatus.SHIPPED,
            external_order_id=external_order_id,
            external_status="SHIPPED",
            tracking_number=f"MTRK{external_order_id[-8:]}",
            carrier="MockExpress",
        )
