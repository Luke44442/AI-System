"""Reusable marketplace adapter architecture.

Every marketplace (Etsy, eBay, TikTok Shop, Pinterest, Google Merchant) is
implemented as a subclass of `MarketplaceAdapter` exposing the same surface:
create / update / inventory / price / delete. The orchestration service in
`service.py` drives all adapters uniformly and persists state to the
`marketplace_listings` table.

Adapters degrade gracefully: when their credentials aren't configured they
return a SKIPPED result instead of raising, so a partially-configured
deployment never crashes a sync run.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Optional


class SyncStatus(str, Enum):
    SUCCESS = "success"
    SKIPPED = "skipped"      # adapter not configured
    FAILED = "failed"
    NOT_SUPPORTED = "not_supported"


class ListingState(str, Enum):
    """Per-platform listing state machine persisted in marketplace_listings.status.

        created → uploaded → published
                       ↘ failed → retrying → published
                                       ↘ dead (after retry budget — dead-letter table)
        pending = adapter not configured yet (credentials missing)
    """
    CREATED = "created"
    UPLOADED = "uploaded"
    PUBLISHED = "published"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD = "dead"
    PENDING = "pending"


@dataclass
class ProductPayload:
    """Normalized product view passed to adapters (decoupled from the ORM)."""
    id: str
    sku: str
    title: str
    description: str
    price: Decimal
    quantity: int
    brand: Optional[str] = None
    category: Optional[str] = None
    product_type: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    url: Optional[str] = None


@dataclass
class SyncResult:
    platform: str
    status: SyncStatus
    listing_id: Optional[str] = None
    listing_url: Optional[str] = None
    message: Optional[str] = None
    raw: Optional[dict] = None

    @property
    def ok(self) -> bool:
        return self.status in (SyncStatus.SUCCESS, SyncStatus.SKIPPED)


class MarketplaceAdapter:
    """Base class. Subclasses set `platform` and implement the API calls."""

    platform: str = "base"
    # Capabilities — subclasses flip these on as they implement them.
    supports_inventory_sync: bool = True
    supports_price_sync: bool = True
    supports_order_sync: bool = False

    def is_configured(self) -> bool:
        """Return True when this adapter has the credentials it needs."""
        raise NotImplementedError

    # -- Listing lifecycle -------------------------------------------------
    def create_listing(self, product: ProductPayload) -> SyncResult:
        raise NotImplementedError

    def update_listing(self, listing_id: str, product: ProductPayload) -> SyncResult:
        raise NotImplementedError

    def delete_listing(self, listing_id: str) -> SyncResult:
        raise NotImplementedError

    def update_inventory(self, listing_id: str, quantity: int) -> SyncResult:
        return SyncResult(self.platform, SyncStatus.NOT_SUPPORTED, message="inventory sync not supported")

    def update_price(self, listing_id: str, price: Decimal) -> SyncResult:
        return SyncResult(self.platform, SyncStatus.NOT_SUPPORTED, message="price sync not supported")

    def fetch_orders(self, since: Optional[str] = None) -> list[dict]:
        return []

    # -- Helpers -----------------------------------------------------------
    def _skipped(self, reason: str = "not configured") -> SyncResult:
        return SyncResult(self.platform, SyncStatus.SKIPPED, message=reason)

    def _failed(self, message: str, raw: Optional[dict] = None) -> SyncResult:
        return SyncResult(self.platform, SyncStatus.FAILED, message=message, raw=raw)

    def _success(self, listing_id: Optional[str] = None, url: Optional[str] = None,
                 raw: Optional[dict] = None) -> SyncResult:
        return SyncResult(self.platform, SyncStatus.SUCCESS, listing_id=listing_id,
                          listing_url=url, raw=raw)
