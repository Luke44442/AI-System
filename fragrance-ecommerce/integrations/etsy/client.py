from __future__ import annotations
import time
from typing import Optional
import httpx
from app.config import settings

ETSY_API_BASE = "https://openapi.etsy.com/v3"

# Transient statuses worth retrying with backoff.
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF_SECONDS = (1, 2, 4)


class EtsyAPIError(Exception):
    """Raised on any non-2xx Etsy response, with status + body for diagnostics."""

    def __init__(self, message: str, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class EtsyClient:
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key or settings.ETSY_API_KEY
        self.access_token = access_token or settings.ETSY_ACCESS_TOKEN
        self._client = httpx.Client(
            base_url=ETSY_API_BASE,
            headers={
                "x-api-key": self.api_key,
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Issue a request with retry + exponential backoff on transient errors."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            if attempt:
                time.sleep(_BACKOFF_SECONDS[min(attempt - 1, len(_BACKOFF_SECONDS) - 1)])
            try:
                resp = self._client.request(method, path, **kwargs)
            except httpx.HTTPError as exc:
                last_exc = exc
                continue
            if resp.status_code in _RETRYABLE_STATUSES:
                last_exc = EtsyAPIError(
                    f"Etsy transient error {resp.status_code} on {method} {path}",
                    status_code=resp.status_code, body=resp.text[:500],
                )
                continue
            if resp.status_code >= 400:
                raise EtsyAPIError(
                    f"Etsy API error {resp.status_code} on {method} {path}: {resp.text[:500]}",
                    status_code=resp.status_code, body=resp.text[:500],
                )
            return resp
        raise EtsyAPIError(f"Etsy request failed after {_MAX_RETRIES} retries: {last_exc}")

    def get_shop(self, shop_id: str) -> dict:
        return self._request("GET", f"/application/shops/{shop_id}").json()

    def list_listings(self, shop_id: str, state: str = "active", limit: int = 25, offset: int = 0) -> dict:
        return self._request(
            "GET", f"/application/shops/{shop_id}/listings",
            params={"state": state, "limit": limit, "offset": offset},
        ).json()

    def get_listing(self, listing_id: str) -> dict:
        return self._request("GET", f"/application/listings/{listing_id}").json()

    def create_listing(self, shop_id: str, payload: dict) -> dict:
        return self._request("POST", f"/application/shops/{shop_id}/listings", json=payload).json()

    def update_listing(self, shop_id: str, listing_id: str, payload: dict) -> dict:
        return self._request(
            "PATCH", f"/application/shops/{shop_id}/listings/{listing_id}", json=payload
        ).json()

    def delete_listing(self, shop_id: str, listing_id: str) -> bool:
        resp = self._request("DELETE", f"/application/shops/{shop_id}/listings/{listing_id}")
        return resp.status_code == 204

    def upload_listing_image(self, shop_id: str, listing_id: str, image_url: str, rank: int = 1) -> dict:
        return self._request(
            "POST", f"/application/shops/{shop_id}/listings/{listing_id}/images",
            json={"url": image_url, "rank": rank},
        ).json()

    def get_shop_receipts(self, shop_id: str, min_created: Optional[int] = None, limit: int = 25) -> dict:
        """Fetch orders (receipts) for order-sync."""
        params: dict = {"limit": limit}
        if min_created:
            params["min_created"] = min_created
        return self._request(
            "GET", f"/application/shops/{shop_id}/receipts", params=params
        ).json()
