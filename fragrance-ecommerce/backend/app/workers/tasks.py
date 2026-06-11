from __future__ import annotations
import asyncio
import logging
from typing import Optional
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_ai_listing_task(self, product_id: str, platform: str = "website"):
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.product import Product
        from app.services.ai_listing import generate_product_listing
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        import uuid

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Product).where(Product.id == uuid.UUID(product_id)).options(selectinload(Product.brand))
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"error": "Product not found"}

            listing = generate_product_listing(
                brand=product.brand.name if product.brand else "",
                product_name=product.name,
                concentration=product.concentration,
                volume_ml=product.volume_ml,
                gender=product.gender,
                top_notes=product.top_notes,
                middle_notes=product.middle_notes,
                base_notes=product.base_notes,
                platform=platform,
            )
            if listing:
                if listing.get("description"):
                    product.description = listing["description"]
                if listing.get("seo_title"):
                    product.seo_title = listing["seo_title"]
                if listing.get("seo_description"):
                    product.seo_description = listing["seo_description"]
                if listing.get("tags"):
                    product.tags = listing["tags"]
                product.ai_generated_listing = True
                await db.commit()
            return {"product_id": product_id, "status": "completed"}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(f"AI listing task failed for {product_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def sync_all_marketplace_listings(self):
    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.marketplaces.service import sync_all_active_products
        async with AsyncSessionLocal() as db:
            return await sync_all_active_products(db)

    try:
        result = _run_async(_run())
        logger.info(f"Marketplace sync complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"Marketplace sync failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_product_to_marketplaces_task(self, product_id: str):
    """Auto-post a single product to all configured marketplaces."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.product import Product
        from app.services.marketplaces.service import sync_product_all
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        import uuid

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Product).where(Product.id == uuid.UUID(product_id)).options(selectinload(Product.brand))
            )
            product = result.scalar_one_or_none()
            if not product:
                return {"error": "Product not found"}
            return await sync_product_all(db, product)

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(f"Product marketplace sync failed for {product_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def refresh_analytics_views():
    async def _run():
        from app.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(text("SELECT refresh_daily_revenue()"))
                await db.execute(text("SELECT refresh_product_performance()"))
                await db.commit()
                logger.info("Analytics views refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh analytics views: {e}")

    _run_async(_run())


@celery_app.task
def update_inventory_status():
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.product import Product
        from sqlalchemy import select, update
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Product)
                .where(Product.inventory_quantity <= 0)
                .values(inventory_status="out_of_stock")
            )
            await db.execute(
                update(Product)
                .where(
                    Product.inventory_quantity > 0,
                    Product.inventory_quantity <= Product.low_stock_threshold,
                )
                .values(inventory_status="low_stock")
            )
            await db.execute(
                update(Product)
                .where(Product.inventory_quantity > Product.low_stock_threshold)
                .values(inventory_status="in_stock")
            )
            await db.commit()

    _run_async(_run())


@celery_app.task
def generate_sitemap():
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.product import Product, Category
        from sqlalchemy import select
        import xml.etree.ElementTree as ET
        from datetime import datetime

        async with AsyncSessionLocal() as db:
            products = await db.execute(select(Product.slug).where(Product.is_active == True))
            categories = await db.execute(select(Category.slug).where(Category.is_active == True))

            product_slugs = [r[0] for r in products]
            category_slugs = [r[0] for r in categories]

            urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")

            def add_url(loc, priority="0.8"):
                url = ET.SubElement(urlset, "url")
                ET.SubElement(url, "loc").text = loc
                ET.SubElement(url, "lastmod").text = datetime.utcnow().strftime("%Y-%m-%d")
                ET.SubElement(url, "priority").text = priority

            add_url("https://aurevia.com/", "1.0")
            add_url("https://aurevia.com/products", "0.9")
            for slug in product_slugs:
                add_url(f"https://aurevia.com/products/{slug}")
            for slug in category_slugs:
                add_url(f"https://aurevia.com/categories/{slug}", "0.7")

            sitemap_xml = ET.tostring(urlset, encoding="unicode", xml_declaration=True)
            logger.info(f"Sitemap generated with {len(product_slugs)} products")
            return sitemap_xml

    return _run_async(_run())


@celery_app.task(bind=True, max_retries=2)
def process_order_fulfillment(self, order_id: str):
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.services.fulfillment import process_paid_order
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        import uuid

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
                .options(selectinload(Order.items), selectinload(Order.customer))
            )
            order = result.scalar_one_or_none()
            if not order:
                return {"error": "Order not found"}
            return await process_paid_order(db, order)

    try:
        return _run_async(_run())
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def place_supplier_order_task(self, order_id: str):
    """Drive a paid order to a terminal supplier state (placed/failed/queued).

    The orchestrator is idempotent, so Celery retries cannot double-order.
    If even the task machinery fails repeatedly, the order is force-queued
    for manual handling rather than left dangling.
    """
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.services.supplier_orchestrator import place_order
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        import uuid

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Order).where(Order.id == uuid.UUID(order_id))
                .options(selectinload(Order.items), selectinload(Order.customer))
            )
            order = result.scalar_one_or_none()
            if not order:
                return {"error": "Order not found"}
            so = await place_order(db, order)
            return {"order_id": order_id, "supplier_order_status": so.status,
                    "external_order_id": so.external_order_id}

    async def _force_queue():
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.services.supplier_orchestrator import fallback_to_manual_queue
        from sqlalchemy import select
        import uuid

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Order).where(Order.id == uuid.UUID(order_id)))
            order = result.scalar_one_or_none()
            if order:
                await fallback_to_manual_queue(
                    db, order, "Supplier ordering task crashed repeatedly — needs human review"
                )

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(f"Supplier order task failed for {order_id}: {exc}")
        if self.request.retries >= self.max_retries:
            try:
                _run_async(_force_queue())
            except Exception as queue_exc:  # last line of defense
                logger.critical(f"Could not even queue order {order_id} manually: {queue_exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def track_supplier_orders_task(self):
    """Poll suppliers for status on all open supplier orders."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.fulfillment import SupplierOrder
        from app.services.supplier_orchestrator import track_order
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(SupplierOrder).where(SupplierOrder.status == "placed").limit(200)
            )
            supplier_orders = rows.scalars().all()
            tracked = 0
            for so in supplier_orders:
                try:
                    await track_order(db, so)
                    tracked += 1
                except Exception as exc:
                    logger.warning("supplier_tracking_error so=%s error=%s", so.id, exc)
            return {"tracked": tracked, "open": len(supplier_orders)}

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(f"Supplier tracking sweep failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def retry_failed_listings():
    """Re-sync marketplace listings whose backoff window has elapsed."""
    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.marketplaces.service import retry_due_listings
        async with AsyncSessionLocal() as db:
            return await retry_due_listings(db)

    result = _run_async(_run())
    logger.info(f"Listing retry sweep: {result}")
    return result


@celery_app.task
def reconcile_stuck_orders():
    """Safety net: any paid order with no supplier_order row gets one dispatched.

    This catches orders that slipped through (e.g. webhook fired while the
    worker was down) — the exact failure mode that used to be silent.
    """
    async def _run():
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.models.fulfillment import SupplierOrder
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(Order.id)
                .outerjoin(SupplierOrder, SupplierOrder.order_id == Order.id)
                .where(
                    Order.payment_status == "paid",
                    Order.fulfillment_status.in_(["unfulfilled", "processing"]),
                    SupplierOrder.id.is_(None),
                )
                .limit(100)
            )
            return [str(r[0]) for r in rows.all()]

    order_ids = _run_async(_run())
    for oid in order_ids:
        place_supplier_order_task.delay(oid)
    if order_ids:
        logger.warning(f"Reconciled {len(order_ids)} stuck paid orders into supplier pipeline")
    return {"dispatched": len(order_ids)}


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def sync_supplier_costs_task(self, supplier_slug: str):
    async def _run():
        from app.database import AsyncSessionLocal
        from app.services.supplier_sync import sync_supplier_costs
        async with AsyncSessionLocal() as db:
            return await sync_supplier_costs(db, supplier_slug)

    try:
        return _run_async(_run())
    except Exception as exc:
        logger.error(f"Supplier sync failed for {supplier_slug}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def sync_all_suppliers():
    """Fan out cost-sync across all active suppliers that have a client."""
    async def _list_suppliers():
        from app.database import AsyncSessionLocal
        from app.models.product import Supplier
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            rows = await db.execute(select(Supplier.slug).where(Supplier.is_active == True))  # noqa: E712
            return [r[0] for r in rows]

    slugs = _run_async(_list_suppliers())
    dispatched = []
    for slug in slugs:
        sync_supplier_costs_task.delay(slug)
        dispatched.append(slug)
    return {"dispatched": dispatched}


@celery_app.task
def bulk_generate_listings(product_ids: list[str], platform: str = "website"):
    results = []
    for pid in product_ids:
        result = generate_ai_listing_task.delay(pid, platform)
        results.append({"product_id": pid, "task_id": result.id})
    return results


# ---------------------------------------------------------------------------
# Email automation tasks
# ---------------------------------------------------------------------------

@celery_app.task
def send_cart_abandonment_emails():
    """Email customers whose carts have been idle for 1–25 hours.

    Uses a sliding window (1h–25h since last update) to avoid re-sending on
    every run without requiring a separate DB column.
    """
    async def _run():
        from datetime import datetime, timedelta, timezone
        from app.database import AsyncSessionLocal
        from app.models.customer import Cart, Customer
        from app.models.product import Product
        from app.services.email import send_cart_abandonment_email
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=25)
        window_end = now - timedelta(hours=1)

        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(Cart)
                .where(
                    Cart.updated_at >= window_start,
                    Cart.updated_at <= window_end,
                    Cart.customer_id.isnot(None),
                )
                .options(
                    selectinload(Cart.items),
                    selectinload(Cart.customer),
                )
            )
            carts = rows.scalars().all()
            sent = 0
            for cart in carts:
                if not cart.items or not cart.customer:
                    continue
                customer = cart.customer
                if not customer.marketing_consent or not customer.is_active:
                    continue

                # Build items list by fetching product names for the cart
                product_ids = [item.product_id for item in cart.items]
                prod_rows = await db.execute(
                    select(Product.id, Product.name, Product.website_price)
                    .where(Product.id.in_(product_ids))
                )
                products_by_id = {p.id: {"name": p.name, "price": p.website_price} for p in prod_rows}
                items = [
                    {
                        "name": products_by_id.get(item.product_id, {}).get("name", "Item"),
                        "quantity": item.quantity,
                        "unit_price": float(products_by_id.get(item.product_id, {}).get("price", 0) or 0),
                    }
                    for item in cart.items
                ]

                try:
                    send_cart_abandonment_email(
                        to=customer.email,
                        first_name=customer.first_name,
                        items=items,
                    )
                    sent += 1
                except Exception as exc:
                    logger.warning("cart_abandonment_email_failed customer=%s error=%s", customer.id, exc)

            logger.info("cart_abandonment_run sent=%d total_carts=%d", sent, len(carts))
            return {"sent": sent, "evaluated": len(carts)}

    return _run_async(_run())


@celery_app.task
def send_review_request_emails():
    """Ask customers to review orders that were fulfilled ~7 days ago."""
    async def _run():
        from datetime import datetime, timedelta, timezone
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.models.customer import Customer
        from app.services.email import send_review_request_email
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        now = datetime.now(timezone.utc)
        # Daily window: orders fulfilled between 7d+1h and 7d ago
        window_start = now - timedelta(days=7, hours=1)
        window_end = now - timedelta(days=7)

        async with AsyncSessionLocal() as db:
            rows = await db.execute(
                select(Order)
                .where(
                    Order.created_at >= window_start,
                    Order.created_at <= window_end,
                    Order.fulfillment_status.in_(["shipped", "fulfilled", "delivered"]),
                    Order.customer_id.isnot(None),
                )
                .options(selectinload(Order.items), selectinload(Order.customer))
            )
            orders = rows.scalars().all()
            sent = 0
            for order in orders:
                customer = order.customer
                if not customer or not customer.marketing_consent or not customer.is_active:
                    continue
                items = [{"name": i.name} for i in order.items]
                try:
                    send_review_request_email(
                        to=customer.email,
                        first_name=customer.first_name,
                        order_number=order.order_number,
                        items=items,
                    )
                    sent += 1
                except Exception as exc:
                    logger.warning("review_request_email_failed order=%s error=%s", order.order_number, exc)

            logger.info("review_request_run sent=%d", sent)
            return {"sent": sent, "evaluated": len(orders)}

    return _run_async(_run())


@celery_app.task
def send_win_back_emails():
    """Re-engage customers whose last order was 90–91 days ago."""
    async def _run():
        from datetime import datetime, timedelta, timezone
        from app.database import AsyncSessionLocal
        from app.models.order import Order
        from app.models.customer import Customer
        from app.services.email import send_win_back_email
        from sqlalchemy import select, func, and_

        now = datetime.now(timezone.utc)
        # Target customers whose most recent order falls in a 1-day window 90 days ago.
        # Running daily ensures each qualifying customer is contacted exactly once.
        window_start = now - timedelta(days=91)
        window_end = now - timedelta(days=90)

        async with AsyncSessionLocal() as db:
            # Subquery: find customers whose last order was in the target window
            last_order_sq = (
                select(Order.customer_id, func.max(Order.created_at).label("last_order"))
                .where(Order.customer_id.isnot(None))
                .group_by(Order.customer_id)
                .subquery()
            )
            rows = await db.execute(
                select(Customer)
                .join(last_order_sq, Customer.id == last_order_sq.c.customer_id)
                .where(
                    last_order_sq.c.last_order >= window_start,
                    last_order_sq.c.last_order <= window_end,
                    Customer.marketing_consent == True,  # noqa: E712
                    Customer.is_active == True,          # noqa: E712
                )
            )
            customers = rows.scalars().all()
            sent = 0
            for customer in customers:
                try:
                    send_win_back_email(
                        to=customer.email,
                        first_name=customer.first_name,
                        days_inactive=90,
                    )
                    sent += 1
                except Exception as exc:
                    logger.warning("win_back_email_failed customer=%s error=%s", customer.id, exc)

            logger.info("win_back_run sent=%d", sent)
            return {"sent": sent, "evaluated": len(customers)}

    return _run_async(_run())
