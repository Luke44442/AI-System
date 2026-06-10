"""Marketplace sync orchestration.

Drives all adapters uniformly and persists state into `marketplace_listings`,
so a product can be auto-posted everywhere with one call and the admin can see
exactly what succeeded, what was skipped (unconfigured), and what failed.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.product import Product
from app.models.marketplace import MarketplaceListing
from app.services.marketplaces.base import ProductPayload, SyncStatus, SyncResult
from app.services.marketplaces import registry

logger = logging.getLogger(__name__)

SITE_URL = "https://aurevia.com"


def product_to_payload(product: Product) -> ProductPayload:
    images = []
    for img in (product.images or []):
        if isinstance(img, dict) and img.get("url"):
            images.append(img["url"])
        elif isinstance(img, str):
            images.append(img)
    brand = product.brand.name if getattr(product, "brand", None) else None
    return ProductPayload(
        id=str(product.id),
        sku=product.sku,
        title=product.name,
        description=product.description or product.seo_description or product.name,
        price=product.marketplace_price or product.website_price or Decimal("0"),
        quantity=product.inventory_quantity or 0,
        brand=brand,
        category=product.fragrance_family or product.style_category,
        product_type=getattr(product, "product_type", None),
        tags=product.tags or [],
        images=images,
        attributes=product.attributes or {},
        url=f"{SITE_URL}/products/{product.slug}",
    )


async def _get_listing(db: AsyncSession, product_id, platform: str) -> MarketplaceListing | None:
    result = await db.execute(
        select(MarketplaceListing).where(
            MarketplaceListing.product_id == product_id,
            MarketplaceListing.platform == platform,
        )
    )
    return result.scalar_one_or_none()


def _apply_result(listing: MarketplaceListing, result: SyncResult, payload: ProductPayload) -> None:
    listing.title = payload.title
    listing.price = payload.price
    listing.quantity = payload.quantity
    listing.last_synced_at = datetime.now(timezone.utc).isoformat()
    if result.status == SyncStatus.SUCCESS:
        listing.status = "active"
        listing.listing_id = result.listing_id or listing.listing_id
        listing.listing_url = result.listing_url or listing.listing_url
        listing.sync_error = None
    elif result.status == SyncStatus.SKIPPED:
        listing.status = "pending"  # awaiting credentials
        listing.sync_error = result.message
    else:  # FAILED / NOT_SUPPORTED
        listing.status = "error"
        listing.sync_error = result.message


async def sync_product_to_platform(db: AsyncSession, product: Product, platform: str) -> SyncResult:
    adapter = registry.get_adapter(platform)
    if adapter is None:
        return SyncResult(platform, SyncStatus.NOT_SUPPORTED, message="unknown platform")

    payload = product_to_payload(product)
    listing = await _get_listing(db, product.id, platform)
    if listing is None:
        listing = MarketplaceListing(product_id=product.id, platform=platform, status="draft")
        db.add(listing)

    # Create vs update based on whether we already have a remote listing id.
    if listing.listing_id:
        result = adapter.update_listing(listing.listing_id, payload)
    else:
        result = adapter.create_listing(payload)

    _apply_result(listing, result, payload)
    await db.commit()
    logger.info("marketplace_sync product=%s platform=%s status=%s", product.sku, platform, result.status)
    return result


async def sync_product_all(db: AsyncSession, product: Product, only_configured: bool = True) -> list[dict]:
    """Auto-post a single product to every (configured) marketplace."""
    platforms = [a.platform for a in (registry.configured_adapters() if only_configured else registry.all_adapters())]
    results = []
    for platform in platforms:
        res = await sync_product_to_platform(db, product, platform)
        results.append({"platform": platform, "status": res.status.value, "message": res.message,
                        "listing_id": res.listing_id})
    return results


async def sync_all_active_products(db: AsyncSession, limit: int = 500) -> dict:
    """Batch sync: push every active product to all configured marketplaces."""
    if not settings.ENABLE_MARKETPLACE_SYNC:
        return {"skipped": "ENABLE_MARKETPLACE_SYNC is off"}

    configured = registry.configured_adapters()
    if not configured:
        return {"skipped": "no marketplaces configured", "platforms": []}

    result = await db.execute(
        select(Product).where(Product.is_active == True)  # noqa: E712
        .options(selectinload(Product.brand)).limit(limit)
    )
    products = result.scalars().all()
    totals = {a.platform: {"success": 0, "failed": 0, "skipped": 0} for a in configured}
    for product in products:
        for adapter in configured:
            res = await sync_product_to_platform(db, product, adapter.platform)
            bucket = "success" if res.status == SyncStatus.SUCCESS else (
                "skipped" if res.status == SyncStatus.SKIPPED else "failed")
            totals[adapter.platform][bucket] += 1
    return {"products": len(products), "platforms": totals}


async def sync_inventory(db: AsyncSession, product: Product) -> list[dict]:
    """Push current inventory to all platforms that already have a listing."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.product_id == product.id)
    )
    listings = result.scalars().all()
    out = []
    for listing in listings:
        adapter = registry.get_adapter(listing.platform)
        if adapter and listing.listing_id:
            res = adapter.update_inventory(listing.listing_id, product.inventory_quantity or 0)
            out.append({"platform": listing.platform, "status": res.status.value})
    return out


async def sync_health(db: AsyncSession) -> dict:
    """Monitoring snapshot: per-platform listing counts by status + failures."""
    rows = await db.execute(
        select(MarketplaceListing.platform, MarketplaceListing.status, func.count())
        .group_by(MarketplaceListing.platform, MarketplaceListing.status)
    )
    by_platform: dict[str, dict] = {}
    for platform, status, count in rows.all():
        by_platform.setdefault(platform, {})[status] = count

    # Recent failures for the dashboard.
    fails = await db.execute(
        select(MarketplaceListing)
        .where(MarketplaceListing.status == "error")
        .order_by(MarketplaceListing.last_synced_at.desc())
        .limit(25)
    )
    failures = [
        {"platform": l.platform, "product_id": str(l.product_id),
         "error": l.sync_error, "last_synced_at": l.last_synced_at}
        for l in fails.scalars().all()
    ]
    return {
        "platforms": registry.platform_status(),
        "listing_counts": by_platform,
        "recent_failures": failures,
    }
