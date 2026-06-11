"""Marketplace sync orchestration with a strict per-platform state machine.

Drives all adapters uniformly and persists state into `marketplace_listings`.
Failures are never silent:
  * every failed attempt increments `sync_attempts`, schedules an exponential-
    backoff retry (`next_sync_at`), and records a system_event;
  * listings that exhaust the retry budget are moved to `dead` and copied into
    `marketplace_dead_letters` for the failures dashboard;
  * a successful sync resets the retry bookkeeping.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.product import Product
from app.models.marketplace import MarketplaceListing
from app.models.fulfillment import MarketplaceDeadLetter
from app.services.events import record_event
from app.services.marketplaces.base import ListingState, ProductPayload, SyncStatus, SyncResult
from app.services.marketplaces import registry

logger = logging.getLogger(__name__)

SITE_URL = "https://aurevia.com"

# Backoff: 5min, 10min, 20min, 40min, 80min — then dead-letter.
RETRY_BASE_MINUTES = 5


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _backoff_minutes(attempts: int) -> int:
    return RETRY_BASE_MINUTES * (2 ** max(attempts - 1, 0))


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


async def _apply_result(
    db: AsyncSession,
    listing: MarketplaceListing,
    result: SyncResult,
    payload: ProductPayload,
    operation: str,
) -> None:
    """State machine transition for one sync attempt. Emits events on failure."""
    listing.title = payload.title
    listing.price = payload.price
    listing.quantity = payload.quantity
    listing.last_synced_at = _now()

    if result.status == SyncStatus.SUCCESS:
        listing.status = ListingState.PUBLISHED.value
        listing.listing_id = result.listing_id or listing.listing_id
        listing.listing_url = result.listing_url or listing.listing_url
        listing.sync_error = None
        listing.sync_attempts = 0
        listing.next_sync_at = None
        # Partial success (e.g. listing created but image upload failed) is
        # surfaced, not buried — it shows up as a warning event.
        if result.message:
            await record_event(
                db, "marketplace_sync_warning", severity="warning",
                message=result.message, listing_id=listing.id,
                product_id=listing.product_id,
                payload={"platform": listing.platform, "operation": operation},
            )
        return

    if result.status == SyncStatus.SKIPPED:
        # Adapter unconfigured — visible as 'pending credentials', not an error.
        listing.status = ListingState.PENDING.value
        listing.sync_error = result.message
        return

    # FAILED / NOT_SUPPORTED — count the attempt, schedule retry or dead-letter.
    listing.sync_attempts = (listing.sync_attempts or 0) + 1
    listing.sync_error = result.message

    max_attempts = settings.MARKETPLACE_MAX_SYNC_ATTEMPTS
    if listing.sync_attempts >= max_attempts:
        listing.status = ListingState.DEAD.value
        listing.next_sync_at = None
        db.add(MarketplaceDeadLetter(
            listing_id=listing.id,
            product_id=listing.product_id,
            platform=listing.platform,
            operation=operation,
            attempts=listing.sync_attempts,
            last_error=result.message,
            payload={"sku": payload.sku, "title": payload.title, "price": str(payload.price)},
        ))
        await record_event(
            db, "marketplace_listing_dead", severity="critical",
            message=f"{listing.platform} listing for {payload.sku} dead-lettered after "
                    f"{listing.sync_attempts} attempts: {result.message}",
            listing_id=listing.id, product_id=listing.product_id,
            payload={"platform": listing.platform, "operation": operation},
        )
    else:
        listing.status = ListingState.RETRYING.value
        retry_at = _now() + timedelta(minutes=_backoff_minutes(listing.sync_attempts))
        listing.next_sync_at = retry_at
        await record_event(
            db, "marketplace_sync_failed", severity="error",
            message=f"{listing.platform} {operation} failed (attempt {listing.sync_attempts}/"
                    f"{max_attempts}): {result.message}",
            listing_id=listing.id, product_id=listing.product_id,
            payload={"platform": listing.platform, "operation": operation,
                     "next_retry_at": retry_at.isoformat()},
        )


async def sync_product_to_platform(db: AsyncSession, product: Product, platform: str) -> SyncResult:
    adapter = registry.get_adapter(platform)
    if adapter is None:
        return SyncResult(platform, SyncStatus.NOT_SUPPORTED, message="unknown platform")

    payload = product_to_payload(product)
    listing = await _get_listing(db, product.id, platform)
    if listing is None:
        listing = MarketplaceListing(product_id=product.id, platform=platform,
                                     status=ListingState.CREATED.value)
        db.add(listing)
        await db.flush()

    # Create vs update based on whether we already have a remote listing id.
    if listing.listing_id:
        operation = "update"
        result = adapter.update_listing(listing.listing_id, payload)
    else:
        operation = "create"
        result = adapter.create_listing(payload)

    await _apply_result(db, listing, result, payload, operation)
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


async def retry_due_listings(db: AsyncSession, limit: int = 100) -> dict:
    """Re-sync listings whose backoff window has elapsed (run from Celery beat)."""
    rows = await db.execute(
        select(MarketplaceListing)
        .where(
            MarketplaceListing.status == ListingState.RETRYING.value,
            MarketplaceListing.next_sync_at.isnot(None),
            MarketplaceListing.next_sync_at <= _now(),
        )
        .limit(limit)
    )
    listings = rows.scalars().all()
    retried = succeeded = 0
    for listing in listings:
        prod_row = await db.execute(
            select(Product).where(Product.id == listing.product_id)
            .options(selectinload(Product.brand))
        )
        product = prod_row.scalar_one_or_none()
        if product is None:
            continue
        retried += 1
        res = await sync_product_to_platform(db, product, listing.platform)
        if res.status == SyncStatus.SUCCESS:
            succeeded += 1
    return {"retried": retried, "succeeded": succeeded}


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
            payload = product_to_payload(product)
            await _apply_result(db, listing, res, payload, "inventory")
            out.append({"platform": listing.platform, "status": res.status.value})
    await db.commit()
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

    # Recent failures (retrying + dead + legacy 'error') for the dashboard.
    fails = await db.execute(
        select(MarketplaceListing)
        .where(MarketplaceListing.status.in_([
            ListingState.RETRYING.value, ListingState.DEAD.value, ListingState.FAILED.value, "error",
        ]))
        .order_by(MarketplaceListing.last_synced_at.desc())
        .limit(25)
    )
    failures = [
        {"platform": l.platform, "product_id": str(l.product_id), "status": l.status,
         "attempts": l.sync_attempts, "error": l.sync_error,
         "next_retry_at": l.next_sync_at, "last_synced_at": l.last_synced_at}
        for l in fails.scalars().all()
    ]

    dead_count = (await db.execute(
        select(func.count()).select_from(MarketplaceDeadLetter)
        .where(MarketplaceDeadLetter.is_resolved == False)  # noqa: E712
    )).scalar_one()

    return {
        "platforms": registry.platform_status(),
        "listing_counts": by_platform,
        "recent_failures": failures,
        "dead_letter_count": dead_count,
    }
