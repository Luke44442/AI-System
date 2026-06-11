"""CJ Dropshipping fulfillment adapter (CJ API v2).

Docs: https://developers.cjdropshipping.com/en/api/introduction.html
Auth: getAccessToken with email + apiKey; token sent as CJ-Access-Token.

Credentials are read from the Supplier row (`credentials` JSON) first, then
fall back to global settings, so multiple CJ accounts can coexist.
"""
from __future__ import annotations
import logging
from typing import Optional

import httpx

from app.config import settings
from app.services.suppliers.base import (
    SupplierFulfillmentAdapter,
    SupplierOrderRequest,
    SupplierOrderResult,
    SupplierOrderStatus,
    SupplierAPIError,
)

logger = logging.getLogger(__name__)

CJ_API_BASE = "https://developers.cjdropshipping.com/api2.0/v1"

# CJ order status → our status
_STATUS_MAP = {
    "CREATED": SupplierOrderStatus.PLACED,
    "IN_CART": SupplierOrderStatus.PLACED,
    "UNPAID": SupplierOrderStatus.PLACED,
    "UNSHIPPED": SupplierOrderStatus.PLACED,
    "SHIPPED": SupplierOrderStatus.SHIPPED,
    "DELIVERED": SupplierOrderStatus.DELIVERED,
    "CANCELLED": SupplierOrderStatus.CANCELLED,
}


class CJDropshippingAdapter(SupplierFulfillmentAdapter):
    name = "cj_dropshipping"

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self.email = credentials.get("email") or settings.CJ_EMAIL
        self.api_key = credentials.get("api_key") or settings.CJ_API_KEY
        self._token: Optional[str] = None

    def is_configured(self) -> bool:
        return bool(self.email and self.api_key)

    # -- HTTP plumbing -------------------------------------------------------
    def _get_token(self) -> str:
        if self._token:
            return self._token
        try:
            resp = httpx.post(
                f"{CJ_API_BASE}/authentication/getAccessToken",
                json={"email": self.email, "password": self.api_key},
                timeout=30,
            )
        except httpx.HTTPError as exc:
            raise SupplierAPIError(f"CJ auth network error: {exc}", retryable=True)
        body = resp.json() if resp.content else {}
        if resp.status_code != 200 or not body.get("result"):
            raise SupplierAPIError(
                f"CJ auth failed: {body.get('message', resp.status_code)}",
                retryable=resp.status_code >= 500,
                raw=body,
            )
        self._token = body["data"]["accessToken"]
        return self._token

    def _request(self, method: str, path: str, json: Optional[dict] = None) -> dict:
        token = self._get_token()
        try:
            resp = httpx.request(
                method,
                f"{CJ_API_BASE}{path}",
                json=json,
                headers={"CJ-Access-Token": token},
                timeout=60,
            )
        except httpx.HTTPError as exc:
            raise SupplierAPIError(f"CJ network error on {path}: {exc}", retryable=True)
        body = resp.json() if resp.content else {}
        if resp.status_code == 429 or resp.status_code >= 500:
            raise SupplierAPIError(
                f"CJ transient error {resp.status_code} on {path}: {body.get('message')}",
                retryable=True, raw=body,
            )
        if resp.status_code != 200 or not body.get("result"):
            # Business rejection (bad SKU, address invalid, out of stock) — not retryable.
            raise SupplierAPIError(
                f"CJ rejected {path}: {body.get('message', resp.status_code)}",
                retryable=False, raw=body,
            )
        return body

    # -- Adapter surface -----------------------------------------------------
    def place_order(self, request: SupplierOrderRequest) -> SupplierOrderResult:
        addr = request.shipping_address or {}
        payload = {
            "orderNumber": request.order_number,
            "shippingZip": addr.get("postal_code", ""),
            "shippingCountryCode": addr.get("country", "US"),
            "shippingCountry": addr.get("country", "US"),
            "shippingProvince": addr.get("state", ""),
            "shippingCity": addr.get("city", ""),
            "shippingAddress": ", ".join(filter(None, [addr.get("line1"), addr.get("line2")])),
            "shippingCustomerName": f"{addr.get('first_name', '')} {addr.get('last_name', '')}".strip(),
            "shippingPhone": addr.get("phone", ""),
            "remark": request.note or "",
            "products": [
                {"vid": item.supplier_sku, "quantity": item.quantity}
                for item in request.items
            ],
        }
        body = self._request("POST", "/shopping/order/createOrderV2", json=payload)
        data = body.get("data") or {}
        external_id = str(data.get("orderId") or data.get("orderNum") or "")
        if not external_id:
            raise SupplierAPIError("CJ returned success but no order id", retryable=False, raw=body)
        return SupplierOrderResult(
            status=SupplierOrderStatus.PLACED,
            external_order_id=external_id,
            external_status=str(data.get("orderStatus") or "CREATED"),
            message="CJ order created",
            raw=body,
        )

    def get_order_status(self, external_order_id: str) -> SupplierOrderResult:
        body = self._request("GET", f"/shopping/order/getOrderDetail?orderId={external_order_id}")
        data = body.get("data") or {}
        cj_status = str(data.get("orderStatus") or "").upper()
        status = _STATUS_MAP.get(cj_status, SupplierOrderStatus.UNKNOWN)
        return SupplierOrderResult(
            status=status,
            external_order_id=external_order_id,
            external_status=cj_status,
            tracking_number=data.get("trackNumber"),
            carrier=data.get("logisticName"),
            tracking_url=f"https://www.cjpacket.com/?trackNumber={data.get('trackNumber')}" if data.get("trackNumber") else None,
            raw=body,
        )
