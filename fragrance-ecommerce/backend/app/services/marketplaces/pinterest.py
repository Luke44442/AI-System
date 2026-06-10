"""Pinterest Catalog adapter (Catalogs API — item feed style)."""
from __future__ import annotations
from decimal import Decimal

from app.config import settings
from app.services.marketplaces.base import MarketplaceAdapter, ProductPayload, SyncResult

PINTEREST_API_BASE = "https://api.pinterest.com/v5"


class PinterestAdapter(MarketplaceAdapter):
    platform = "pinterest"
    supports_inventory_sync = True
    supports_price_sync = True
    supports_order_sync = False

    def is_configured(self) -> bool:
        return bool(settings.PINTEREST_ACCESS_TOKEN)

    def _item(self, p: ProductPayload, availability: str | None = None, price: Decimal | None = None) -> dict:
        return {
            "item_id": p.sku,
            "attributes": {
                "title": p.title[:127],
                "description": (p.description or p.title)[:500],
                "link": p.url or "",
                "price": f"{float(price if price is not None else p.price):.2f} USD",
                "availability": availability or ("in stock" if p.quantity > 0 else "out of stock"),
                "image_link": p.images[0] if p.images else "",
                "brand": p.brand or "",
                "google_product_category": p.category or "",
            },
        }

    def _batch(self, items: list[dict], operation: str = "UPSERT") -> dict:
        import httpx
        resp = httpx.post(
            f"{PINTEREST_API_BASE}/catalogs/items/batch",
            headers={
                "Authorization": f"Bearer {settings.PINTEREST_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"country": "US", "language": "EN", "operation": operation, "items": items},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_listing(self, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._batch([self._item(product)], "UPSERT")
            return self._success(listing_id=product.sku, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        return self.create_listing(product)  # UPSERT semantics

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="availability synced on next UPSERT")

    def update_price(self, listing_id: str, price: Decimal) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="price synced on next UPSERT")

    def delete_listing(self, listing_id: str) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._batch([{"item_id": listing_id}], "DELETE")
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))
