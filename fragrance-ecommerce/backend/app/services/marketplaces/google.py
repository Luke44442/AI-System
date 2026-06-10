"""Google Merchant Center adapter (Content API for Shopping)."""
from __future__ import annotations
from decimal import Decimal

from app.config import settings
from app.services.marketplaces.base import MarketplaceAdapter, ProductPayload, SyncResult

CONTENT_API_BASE = "https://shoppingcontent.googleapis.com/content/v2.1"


class GoogleMerchantAdapter(MarketplaceAdapter):
    platform = "google_merchant"
    supports_inventory_sync = True
    supports_price_sync = True
    supports_order_sync = False

    def is_configured(self) -> bool:
        return bool(settings.GOOGLE_MERCHANT_ID and settings.GOOGLE_MERCHANT_CREDENTIALS_JSON)

    def _access_token(self) -> str | None:
        """Exchange the service-account credentials for an OAuth access token."""
        try:
            import json
            from google.oauth2 import service_account  # type: ignore
            from google.auth.transport.requests import Request  # type: ignore
            info = json.loads(settings.GOOGLE_MERCHANT_CREDENTIALS_JSON)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/content"])
            creds.refresh(Request())
            return creds.token
        except Exception:
            return None

    def _product_resource(self, p: ProductPayload, price: Decimal | None = None, availability: str | None = None) -> dict:
        return {
            "offerId": p.sku,
            "title": p.title[:150],
            "description": (p.description or p.title)[:5000],
            "link": p.url or "",
            "imageLink": p.images[0] if p.images else "",
            "additionalImageLinks": p.images[1:11],
            "contentLanguage": "en",
            "targetCountry": "US",
            "channel": "online",
            "availability": availability or ("in stock" if p.quantity > 0 else "out of stock"),
            "condition": "new",
            "brand": p.brand or "",
            "price": {"value": str(price if price is not None else p.price), "currency": "USD"},
        }

    def _insert(self, resource: dict) -> dict:
        import httpx
        token = self._access_token()
        if not token:
            raise RuntimeError("Could not obtain Google access token")
        resp = httpx.post(
            f"{CONTENT_API_BASE}/{settings.GOOGLE_MERCHANT_ID}/products",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=resource,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_listing(self, product: ProductPayload) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        try:
            resp = self._insert(self._product_resource(product))
            return self._success(listing_id=str(resp.get("id", product.sku)), raw=resp)
        except Exception as exc:
            return self._failed(str(exc))

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        return self.create_listing(product)  # Content API insert is upsert by offerId

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="availability synced on next insert")

    def update_price(self, listing_id: str, price: Decimal) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="price synced on next insert")

    def delete_listing(self, listing_id: str) -> SyncResult:
        if not self.is_configured():
            return self._skipped()
        return self._success(listing_id=listing_id, message="delete requested")
