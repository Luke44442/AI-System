from __future__ import annotations
from typing import Optional
import httpx
from app.config import settings

ETSY_API_BASE = "https://openapi.etsy.com/v3"


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

    def get_shop(self, shop_id: str) -> dict:
        return self._client.get(f"/application/shops/{shop_id}").json()

    def list_listings(self, shop_id: str, state: str = "active", limit: int = 25, offset: int = 0) -> dict:
        return self._client.get(
            f"/application/shops/{shop_id}/listings",
            params={"state": state, "limit": limit, "offset": offset},
        ).json()

    def get_listing(self, listing_id: str) -> dict:
        return self._client.get(f"/application/listings/{listing_id}").json()

    def create_listing(self, shop_id: str, payload: dict) -> dict:
        resp = self._client.post(f"/application/shops/{shop_id}/listings", json=payload)
        resp.raise_for_status()
        return resp.json()

    def update_listing(self, shop_id: str, listing_id: str, payload: dict) -> dict:
        resp = self._client.patch(f"/application/shops/{shop_id}/listings/{listing_id}", json=payload)
        resp.raise_for_status()
        return resp.json()

    def delete_listing(self, shop_id: str, listing_id: str) -> bool:
        resp = self._client.delete(f"/application/shops/{shop_id}/listings/{listing_id}")
        return resp.status_code == 204

    def upload_listing_image(self, shop_id: str, listing_id: str, image_url: str) -> dict:
        resp = self._client.post(
            f"/application/shops/{shop_id}/listings/{listing_id}/images",
            json={"url": image_url, "rank": 1},
        )
        resp.raise_for_status()
        return resp.json()
