"""Supplier catalog sync.

Polls a supplier's catalog (via the automation supplier clients) and reconciles
it against our products: records cost changes into supplier_cost_history and
raises pricing_alerts when landed cost rises materially.

Designed to be supplier-agnostic: register new suppliers in SUPPLIER_CLIENTS.
"""
from __future__ import annotations
import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, Supplier
from app.models.analytics import SupplierCostHistory, PricingAlert

logger = logging.getLogger(__name__)

COST_INCREASE_ALERT_THRESHOLD = Decimal("0.05")  # 5%


def _load_supplier_client(supplier_slug: str, credentials: dict):
    """Return an instantiated supplier client, or None if unavailable."""
    try:
        if supplier_slug in ("orient-dig", "orientdig"):
            from automation.suppliers.orientdig import OrientDigSupplier
            return OrientDigSupplier(credentials or {})
        if supplier_slug in ("cnshopper", "cn-shopper"):
            from automation.suppliers.cnshopper import CNShopperSupplier
            return CNShopperSupplier(credentials or {})
    except Exception as exc:  # pragma: no cover - import/network issues
        logger.error("supplier_client_load_failed slug=%s error=%s", supplier_slug, exc)
    return None


async def sync_supplier_costs(db: AsyncSession, supplier_slug: str, limit: int = 200) -> dict:
    """Reconcile our products' costs against the live supplier catalog."""
    sup_result = await db.execute(select(Supplier).where(Supplier.slug == supplier_slug))
    supplier = sup_result.scalar_one_or_none()
    if not supplier:
        return {"error": f"Supplier '{supplier_slug}' not found"}

    client = _load_supplier_client(supplier_slug, supplier.credentials or {})
    if client is None:
        return {"error": f"No client available for supplier '{supplier_slug}'"}

    # Fetch live catalog keyed by supplier SKU.
    try:
        catalog = client.fetch_catalog()
    except Exception as exc:  # pragma: no cover
        logger.error("supplier_catalog_fetch_failed slug=%s error=%s", supplier_slug, exc)
        return {"error": f"Catalog fetch failed: {exc}"}

    catalog_by_sku = {getattr(sp, "supplier_sku", None): sp for sp in catalog if getattr(sp, "supplier_sku", None)}

    products_result = await db.execute(
        select(Product).where(Product.supplier_id == supplier.id).limit(limit)
    )
    products = products_result.scalars().all()

    checked = changed = alerts = 0
    for product in products:
        sp = catalog_by_sku.get(product.supplier_sku)
        if not sp:
            continue
        checked += 1
        new_cost = Decimal(str(getattr(sp, "cost", None) or getattr(sp, "price", 0) or 0))
        old_cost = product.supplier_cost or Decimal("0")
        if new_cost <= 0 or new_cost == old_cost:
            continue

        change_pct = ((new_cost - old_cost) / old_cost * 100) if old_cost > 0 else Decimal("0")
        db.add(SupplierCostHistory(
            supplier_id=supplier.id, product_id=product.id,
            old_cost=old_cost, new_cost=new_cost,
            change_pct=change_pct, source="auto_sync",
        ))
        product.supplier_cost = new_cost
        changed += 1

        # Alert on material cost increases that erode margin.
        if old_cost > 0 and change_pct >= COST_INCREASE_ALERT_THRESHOLD * 100:
            db.add(PricingAlert(
                product_id=product.id,
                alert_type="cost_increase",
                message=f"Supplier cost rose {change_pct:.1f}% (${old_cost} → ${new_cost}) for {product.name}",
                current_value=new_cost,
                threshold_value=old_cost,
            ))
            alerts += 1

    await db.commit()
    logger.info("supplier_sync_complete slug=%s checked=%s changed=%s alerts=%s",
                supplier_slug, checked, changed, alerts)
    return {"supplier": supplier_slug, "checked": checked, "changed": changed, "alerts_created": alerts}
