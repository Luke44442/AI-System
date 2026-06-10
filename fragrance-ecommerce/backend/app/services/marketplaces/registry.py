"""Adapter registry — single place to discover and instantiate adapters."""
from __future__ import annotations

from app.services.marketplaces.base import MarketplaceAdapter
from app.services.marketplaces.etsy import EtsyAdapter
from app.services.marketplaces.ebay import EbayAdapter
from app.services.marketplaces.tiktok import TikTokShopAdapter
from app.services.marketplaces.pinterest import PinterestAdapter
from app.services.marketplaces.google import GoogleMerchantAdapter

_ADAPTERS: dict[str, type[MarketplaceAdapter]] = {
    EtsyAdapter.platform: EtsyAdapter,
    EbayAdapter.platform: EbayAdapter,
    TikTokShopAdapter.platform: TikTokShopAdapter,
    PinterestAdapter.platform: PinterestAdapter,
    GoogleMerchantAdapter.platform: GoogleMerchantAdapter,
}


def all_platforms() -> list[str]:
    return list(_ADAPTERS.keys())


def get_adapter(platform: str) -> MarketplaceAdapter | None:
    cls = _ADAPTERS.get(platform)
    return cls() if cls else None


def all_adapters() -> list[MarketplaceAdapter]:
    return [cls() for cls in _ADAPTERS.values()]


def configured_adapters() -> list[MarketplaceAdapter]:
    """Adapters whose credentials are present — the ones that will actually post."""
    return [a for a in all_adapters() if a.is_configured()]


def platform_status() -> list[dict]:
    """Capability + configuration snapshot for the monitoring dashboard."""
    out = []
    for a in all_adapters():
        out.append({
            "platform": a.platform,
            "configured": a.is_configured(),
            "supports_inventory_sync": a.supports_inventory_sync,
            "supports_price_sync": a.supports_price_sync,
            "supports_order_sync": a.supports_order_sync,
        })
    return out
