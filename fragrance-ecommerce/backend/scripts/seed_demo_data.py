"""Seed demo data for a full walkthrough: product photos, admin user, orders
in every lifecycle state, supplier queue items, marketplace listings, system
events, and a pricing alert. Idempotent-ish (safe to re-run after a wipe)."""
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.core.auth import hash_password
from app.models.product import Product, Supplier
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.marketplace import MarketplaceListing
from app.models.analytics import PricingAlert, OrderProfitability
from app.models.fulfillment import SupplierOrder, SystemEvent
from app.services.pricing_intelligence import calculate_order_profitability

# product slug fragment -> demo image
IMAGE_BY_NAME = {
    "N°5": "/demo/chanel-no5.jpg",
    "Sauvage": "/demo/dior-sauvage.jpg",
    "Black Orchid": "/demo/tf-black-orchid.jpg",
    "Black Opium": "/demo/ysl-black-opium.jpg",
    "Aventus": "/demo/creed-aventus.jpg",
    "Eros": "/demo/versace-eros.jpg",
    "Bloom": "/demo/gucci-bloom.jpg",
    "Acqua di Gio Profumo": "/demo/armani-adg.jpg",
}

ADDR = {
    "first_name": "Olivia", "last_name": "Bennett",
    "address1": "12 Mercer Street", "city": "New York", "state": "NY",
    "postal_code": "10013", "country": "US", "phone": "+1 212 555 0100",
}

now = datetime.now(timezone.utc)


async def main():
    async with AsyncSessionLocal() as db:
        # ----- supplier (mock adapter so the auto path is demonstrable) -----
        sup = (await db.execute(select(Supplier).where(Supplier.slug == "luxe-source"))).scalar_one_or_none()
        if not sup:
            sup = Supplier(name="LuxeSource Trading", slug="luxe-source", type="mock",
                           default_shipping_cost=Decimal("8"), avg_processing_days=2,
                           avg_shipping_days=9, reliability_score=Decimal("4.6"))
            db.add(sup)
            await db.flush()

        # ----- attach images + supplier + scarcity to seeded products -----
        products = (await db.execute(select(Product))).scalars().all()
        by_name = {}
        for p in products:
            img = IMAGE_BY_NAME.get(p.name)
            if img:
                p.images = [{"url": img, "is_primary": True}]
            p.supplier_id = sup.id
            p.supplier_sku = f"LS-{p.sku[:18]}"
            by_name[p.name] = p
        # scarcity layer: a couple of low-stock items
        if "Aventus" in by_name:
            by_name["Aventus"].inventory_quantity = 1
            by_name["Aventus"].inventory_status = "low_stock"
        if "Black Orchid" in by_name:
            by_name["Black Orchid"].inventory_quantity = 3
            by_name["Black Orchid"].inventory_status = "low_stock"

        # ----- admin + a customer -----
        admin = (await db.execute(select(Customer).where(Customer.email == "admin@aurevia.com"))).scalar_one_or_none()
        if not admin:
            admin = Customer(email="admin@aurevia.com", password_hash=hash_password("Aurevia!Demo42"),
                             first_name="Ava", last_name="Sterling", is_admin=True,
                             is_active=True)
            db.add(admin)
        shopper = (await db.execute(select(Customer).where(Customer.email == "olivia@example.com"))).scalar_one_or_none()
        if not shopper:
            shopper = Customer(email="olivia@example.com", password_hash=hash_password("Shopper!Demo42"),
                               first_name="Olivia", last_name="Bennett", is_active=True,
                               marketing_consent=True, order_count=3, total_spent=Decimal("741.20"))
            db.add(shopper)
        await db.flush()

        # ----- orders across the lifecycle -----
        def mk_order(num, product, qty, channel, status, pay, fulfill, created_days_ago, tracking=None):
            unit = product.website_price or Decimal("120")
            sub = unit * qty
            ship = Decimal("12.95")
            total = sub + ship
            o = Order(
                order_number=num, customer_id=shopper.id, customer_name="Olivia Bennett",
                channel=channel, status=status, payment_status=pay, fulfillment_status=fulfill,
                subtotal=sub, shipping_amount=ship, tax_amount=Decimal("0"),
                discount_amount=Decimal("0"), total=total,
                supplier_cost_total=(product.supplier_cost or Decimal("30")) * qty,
                profit_amount=total - (product.supplier_cost or Decimal("30")) * qty - ship,
                shipping_address=ADDR, supplier_id=sup.id,
                tracking_number=tracking, carrier="DHL Express" if tracking else None,
                items=[OrderItem(product_id=product.id, sku=product.sku, name=product.name,
                                 image_url=(product.images or [{}])[0].get("url"),
                                 quantity=qty, unit_price=unit,
                                 supplier_cost=product.supplier_cost or Decimal("30"),
                                 total=unit * qty, supplier_sku=product.supplier_sku)],
            )
            o.created_at = now - timedelta(days=created_days_ago)
            db.add(o)
            return o

        sauvage = by_name.get("Sauvage")
        n5 = by_name.get("N°5")
        aventus = by_name.get("Aventus")
        eros = by_name.get("Eros")
        opium = by_name.get("Black Opium")

        o_shipped = mk_order("AUR-100231", sauvage, 1, "website", "shipped", "paid", "shipped", 4, tracking="DH4482011937US")
        o_placed = mk_order("AUR-100232", n5, 1, "etsy", "processing", "paid", "processing", 1)
        o_queue = mk_order("AUR-100233", aventus, 1, "website", "processing", "paid", "processing", 0)
        o_failed = mk_order("AUR-100234", eros, 2, "website", "processing", "paid", "processing", 0)
        o_pending = mk_order("AUR-100235", opium, 1, "website", "pending", "pending", "unfulfilled", 0)
        await db.flush()

        # profitability snapshots (feeds the analytics overview)
        for o in (o_shipped, o_placed, o_queue, o_failed):
            db.add(OrderProfitability(order_id=o.id, **calculate_order_profitability(
                o.total, o.supplier_cost_total, o.shipping_amount, o.channel)))

        # ----- supplier orders: shipped / placed / manual queue / failed -----
        db.add(SupplierOrder(order_id=o_shipped.id, supplier_id=sup.id, status="shipped",
                             external_order_id="MOCK-7F3KQ2A9X1", external_status="SHIPPED",
                             tracking_number="DH4482011937US", carrier="DHL Express",
                             attempts=1, resolved_by="auto",
                             last_attempt_at=now - timedelta(days=4)))
        db.add(SupplierOrder(order_id=o_placed.id, supplier_id=sup.id, status="placed",
                             external_order_id="MOCK-2B8WN5C3R7", external_status="CREATED",
                             attempts=1, resolved_by="auto",
                             last_attempt_at=now - timedelta(hours=20)))
        db.add(SupplierOrder(order_id=o_queue.id, supplier_id=sup.id, status="manual_queue",
                             queued_reason="Supplier 'LuxeSource Trading' stock check returned 0 units for LS-CR-AVENTUS — needs manual sourcing",
                             attempts=0))
        db.add(SupplierOrder(order_id=o_failed.id, supplier_id=sup.id, status="failed",
                             failure_reason="Supplier order failed after 4 attempts: CJ transient error 503 on /shopping/order/createOrderV2: upstream timeout",
                             attempts=4, last_attempt_at=now - timedelta(hours=2)))

        # ----- marketplace listings in every state -----
        def listing(prod, platform, status, listing_id=None, attempts=0, err=None, next_retry=None):
            l = MarketplaceListing(
                product_id=prod.id, platform=platform, status=status,
                listing_id=listing_id, title=f"{prod.name}", price=prod.marketplace_price,
                quantity=prod.inventory_quantity, sync_attempts=attempts, sync_error=err,
                listing_url=f"https://www.etsy.com/listing/{listing_id}" if (listing_id and platform == "etsy") else None,
                last_synced_at=now - timedelta(minutes=40),
                next_sync_at=next_retry,
            )
            db.add(l)
            return l

        for prod in (n5, sauvage, opium, by_name.get("Bloom")):
            if prod:
                listing(prod, "etsy", "published", listing_id=str(170000000 + hash(prod.sku) % 9999999))
        if aventus:
            listing(aventus, "etsy", "retrying", attempts=2,
                    err="Etsy API error 400: taxonomy_id is invalid for this category",
                    next_retry=now + timedelta(minutes=12))
        if eros:
            l_dead = listing(eros, "etsy", "dead", attempts=5,
                             err="Etsy API error 403: shop is suspended pending verification")
        if by_name.get("Black Orchid"):
            listing(by_name["Black Orchid"], "ebay", "pending")
            listing(by_name["Black Orchid"], "tiktok_shop", "pending")
        await db.flush()

        # dead letter for the dead listing
        from app.models.fulfillment import MarketplaceDeadLetter
        db.add(MarketplaceDeadLetter(listing_id=l_dead.id, product_id=eros.id, platform="etsy",
                                     operation="create", attempts=5,
                                     last_error="Etsy API error 403: shop is suspended pending verification",
                                     payload={"sku": eros.sku, "title": eros.name}))

        # ----- system events: full lifecycle for one order + recent errors -----
        def event(t, sev, msg, order=None, mins_ago=0):
            e = SystemEvent(event_type=t, severity=sev, message=msg,
                            order_id=order.id if order else None, payload={})
            e.created_at = now - timedelta(minutes=mins_ago)
            db.add(e)

        event("order_created", "info", "Order AUR-100232 created via etsy", o_placed, 1450)
        event("order_fulfillment_started", "info", "Order AUR-100232 entered fulfillment", o_placed, 1448)
        event("supplier_order_placed", "info", "Supplier order MOCK-2B8WN5C3R7 placed with LuxeSource Trading", o_placed, 1446)
        event("order_created", "info", "Order AUR-100234 created via website", o_failed, 260)
        event("order_fulfillment_started", "info", "Order AUR-100234 entered fulfillment", o_failed, 258)
        event("supplier_api_call_failed", "warning", "CJ transient error 503 on createOrderV2 (attempt 2)", o_failed, 200)
        event("supplier_order_failed", "critical", "Supplier order failed after 4 attempts: upstream timeout", o_failed, 120)
        event("supplier_order_queued_manual", "warning",
              "Supplier stock check returned 0 units for LS-CR-AVENTUS — needs manual sourcing", o_queue, 45)
        event("marketplace_sync_failed", "error",
              "etsy create failed (attempt 2/5): taxonomy_id is invalid for this category", None, 38)
        event("marketplace_listing_dead", "critical",
              "etsy listing for VS-EROS dead-lettered after 5 attempts: shop suspended pending verification", None, 30)
        event("order_shipped", "info", "Order AUR-100231 shipped via DHL Express (DH4482011937US)", o_shipped, 5600)

        # ----- pricing alert -----
        if aventus:
            db.add(PricingAlert(product_id=aventus.id, alert_type="cost_increase",
                                message="Supplier cost rose 11.8% ($85.00 → $95.00) for Aventus — worst-case margin now 9.4%",
                                current_value=Decimal("95"), threshold_value=Decimal("85")))
        if eros:
            db.add(PricingAlert(product_id=eros.id, alert_type="low_margin",
                                message="Net margin is 24.1%, below the 30% minimum threshold on eBay after 13.25% final value fee.",
                                current_value=Decimal("24.1"), threshold_value=Decimal("30")))

        await db.commit()
        print("Demo data seeded: 8 products w/ photos, admin@aurevia.com / Aurevia!Demo42,")
        print("5 orders, 4 supplier orders (shipped/placed/queued/failed), 8 listings, events, alerts.")


if __name__ == "__main__":
    asyncio.run(main())
