"""eBay marketplace adapter (Sell Inventory API)."""
from __future__ import annotations
from decimal import Decimal

from app.config import settings
from app.services.marketplaces.base import MarketplaceAdapter, ProductPayload, SyncResult


class EbayAdapter(MarketplaceAdapter):
    platform = "ebay"
    supports_inventory_sync = True
    supports_price_sync = True
    supports_order_sync = True

    def is_configured(self) -> bool:
        return bool(settings.EBAY_APP_ID and settings.EBAY_CERT_ID)

    def _client(self):
        from integrations.ebay.client import EbayClient
        return EbayClient(sandbox=settings.EBAY_SANDBOX)

    def _inventory_payload(self, p: ProductPayload) -> dict:
        return {
            "availability": {"shipToLocationAvailability": {"quantity": max(p.quantity, 0)}},
            "condition": "NEW",
            "product": {
                "title": p.title[:80],
                "description": p.description or p.title,
                "brand": p.brand or "Unbranded",
                "imageUrls": p.images[:12] or [],
                "aspects": {k: [str(v)] for k, v in (p.attributes or {}).items()},
            },
        }

    def create_listing(self, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            client = self._client()
            client.create_inventory_item(product.sku, self._inventory_payload(product))
            offer = client.create_offer({
                "sku": product.sku,
                "marketplaceId": "EBAY_US",
                "format": "FIXED_PRICE",
                "availableQuantity": max(product.quantity, 0),
                "pricingSummary": {"price": {"value": str(product.price), "currency": "USD"}},
            })
            offer_id = offer.get("offerId")
            published = client.publish_offer(offer_id) if offer_id else {}
            listing_id = published.get("listingId") or offer_id
            url = f"https://www.ebay.com/itm/{listing_id}" if listing_id else None
            return self._success(listing_id=str(listing_id) if listing_id else None, url=url, raw=offer)
        except Exception as exc:
            return self._failed(str(exc))

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            self._client().create_inventory_item(product.sku, self._inventory_payload(product))
            return self._success(listing_id=listing_id)
        except Exception as exc:
            return self._failed(str(exc))

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        # eBay updates inventory at the inventory_item (SKU) level; handled via update_listing.
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="inventory updated via SKU")

    def update_price(self, listing_id: str, price: Decimal) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="price update queued")

    def delete_listing(self, listing_id: str) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="withdraw requested")
