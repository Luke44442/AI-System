"""Etsy marketplace adapter (Open API v3)."""
from __future__ import annotations
from decimal import Decimal

from app.config import settings
from app.services.marketplaces.base import MarketplaceAdapter, ProductPayload, SyncResult


class EtsyAdapter(MarketplaceAdapter):
    platform = "etsy"
    supports_inventory_sync = True
    supports_price_sync = True
    supports_order_sync = True

    def is_configured(self) -> bool:
        return bool(settings.ETSY_API_KEY and settings.ETSY_ACCESS_TOKEN and settings.ETSY_SHOP_ID)

    def _client(self):
        from integrations.etsy.client import EtsyClient
        return EtsyClient()

    def _build_payload(self, p: ProductPayload) -> dict:
        return {
            "quantity": max(p.quantity, 1),
            "title": p.title[:140],
            "description": p.description or p.title,
            "price": float(p.price),
            "who_made": "someone_else",
            "when_made": "2020_2024",
            "taxonomy_id": 1,  # generic; refine per real Etsy taxonomy
            "tags": (p.tags or [])[:13],
            "should_auto_renew": True,
            "state": "active",
        }

    def create_listing(self, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            client = self._client()
            resp = client.create_listing(settings.ETSY_SHOP_ID, self._build_payload(product))
            listing_id = str(resp.get("listing_id") or resp.get("results", [{}])[0].get("listing_id", ""))
            if listing_id and product.images:
                try:
                    client.upload_listing_image(settings.ETSY_SHOP_ID, listing_id, product.images[0])
                except Exception:
                    pass
            url = f"https://www.etsy.com/listing/{listing_id}" if listing_id else None
            return self._success(listing_id=listing_id or None, url=url, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._client().update_listing(settings.ETSY_SHOP_ID, listing_id, self._build_payload(product))
            return self._success(listing_id=listing_id, url=f"https://www.etsy.com/listing/{listing_id}", raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._client().update_listing(settings.ETSY_SHOP_ID, listing_id, {"quantity": max(quantity, 0)})
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_price(self, listing_id: str, price: Decimal) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._client().update_listing(settings.ETSY_SHOP_ID, listing_id, {"price": float(price)})
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def delete_listing(self, listing_id: str) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            self._client().delete_listing(settings.ETSY_SHOP_ID, listing_id)
            return self._success(listing_id=listing_id)
        except Exception as exc:
            return self._failed(str(exc))
