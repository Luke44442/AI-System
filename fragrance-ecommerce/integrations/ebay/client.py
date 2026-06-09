from __future__ import annotations
import base64
from typing import Optional
import httpx
from app.config import settings

EBAY_SANDBOX_URL = "https://api.sandbox.ebay.com"
EBAY_PROD_URL = "https://api.ebay.com"


class EbayClient:
    def __init__(self, sandbox: bool = False):
        self.base_url = EBAY_SANDBOX_URL if sandbox else EBAY_PROD_URL
        self._oauth_token: Optional[str] = None

    def _get_oauth_token(self) -> str:
        if self._oauth_token:
            return self._oauth_token
        credentials = base64.b64encode(
            f"{settings.EBAY_APP_ID}:{settings.EBAY_CERT_ID}".encode()
        ).decode()
        resp = httpx.post(
            f"{self.base_url}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials", "scope": "https://api.ebay.com/oauth/api_scope"},
            timeout=30,
        )
        resp.raise_for_status()
        self._oauth_token = resp.json()["access_token"]
        return self._oauth_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_oauth_token()}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

    def create_inventory_item(self, sku: str, payload: dict) -> bool:
        resp = httpx.put(
            f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        return resp.status_code in (200, 204)

    def create_offer(self, payload: dict) -> dict:
        resp = httpx.post(
            f"{self.base_url}/sell/inventory/v1/offer",
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def publish_offer(self, offer_id: str) -> dict:
        resp = httpx.post(
            f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_offer(self, offer_id: str) -> dict:
        resp = httpx.get(
            f"{self.base_url}/sell/inventory/v1/offer/{offer_id}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
