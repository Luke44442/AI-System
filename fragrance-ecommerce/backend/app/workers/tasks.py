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
    logger.info("Running marketplace listing sync")
    return {"status": "sync_scheduled"}


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
