from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class SupplierOrderStatus(str, Enum):
    PLACED = "placed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class SupplierAPIError(Exception):
    """Raised by adapters on API failures. `retryable` drives the retry loop."""

    def __init__(self, message: str, *, retryable: bool = True, raw: Optional[dict] = None):
        super().__init__(message)
        self.retryable = retryable
        self.raw = raw or {}


@dataclass
class SupplierOrderItem:
    supplier_sku: str
    quantity: int
    name: str = ""
    unit_cost: Decimal = Decimal("0")


@dataclass
class SupplierOrderRequest:
    order_number: str
    items: list[SupplierOrderItem]
    shipping_address: dict  # first_name, last_name, line1, line2, city, state, postal_code, country, phone
    note: Optional[str] = None


@dataclass
class SupplierOrderResult:
    status: SupplierOrderStatus
    external_order_id: Optional[str] = None
    external_status: Optional[str] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    tracking_url: Optional[str] = None
    message: Optional[str] = None
    raw: dict = field(default_factory=dict)


class SupplierFulfillmentAdapter:
    """Base class for supplier order placement. Subclasses must not swallow
    errors — raise SupplierAPIError so the orchestrator can retry or queue."""

    name: str = "base"

    def __init__(self, credentials: dict):
        self.credentials = credentials or {}

    def is_configured(self) -> bool:
        raise NotImplementedError

    def place_order(self, request: SupplierOrderRequest) -> SupplierOrderResult:
        raise NotImplementedError

    def get_order_status(self, external_order_id: str) -> SupplierOrderResult:
        raise NotImplementedError
