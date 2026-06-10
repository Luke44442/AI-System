"""TikTok Shop adapter (Product API)."""
from __future__ import annotations

from app.config import settings
from app.services.marketplaces.base import MarketplaceAdapter, ProductPayload, SyncResult

TIKTOK_API_BASE = "https://open-api.tiktokglobalshop.com"


class TikTokShopAdapter(MarketplaceAdapter):
    platform = "tiktok_shop"
    supports_inventory_sync = True
    supports_price_sync = True
    supports_order_sync = True

    def is_configured(self) -> bool:
        return bool(settings.TIKTOK_SHOP_APP_KEY and settings.TIKTOK_SHOP_ACCESS_TOKEN)

    def _post(self, path: str, payload: dict) -> dict:
        import httpx
        resp = httpx.post(
            f"{TIKTOK_API_BASE}{path}",
            headers={
                "x-tts-access-token": settings.TIKTOK_SHOP_ACCESS_TOKEN,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _build_payload(self, p: ProductPayload) -> dict:
        return {
            "product_name": p.title[:255],
            "description": p.description or p.title,
            "category_id": "600001",  # placeholder taxonomy; map per real catalog
            "brand_id": p.brand,
            "main_images": [{"uri": img} for img in p.images[:9]],
            "skus": [{
                "seller_sku": p.sku,
                "price": {"amount": str(p.price), "currency": "USD"},
                "inventory": [{"quantity": max(p.quantity, 0)}],
            }],
        }

    def create_listing(self, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._post("/product/202309/products", self._build_payload(product))
            listing_id = str((resp.get("data") or {}).get("product_id", "") or "")
            return self._success(listing_id=listing_id or None, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            payload = self._build_payload(product)
            payload["product_id"] = listing_id
            resp = self._post("/product/202309/products/update", payload)
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._post("/product/202309/products/inventory/update", {
                "product_id": listing_id,
                "skus": [{"inventory": [{"quantity": max(quantity, 0)}]}],
            })
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def delete_listing(self, listing_id: str) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._post("/product/202309/products/deactivate", {"product_ids": [listing_id]})
            return self._success(listing_id=listing_id, raw=resp)
        except Exception as exc:
            return self._failed(str(exc))
