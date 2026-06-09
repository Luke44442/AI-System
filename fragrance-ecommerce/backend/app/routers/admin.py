from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.product import Product, Brand
from app.models.order import Order
from app.models.customer import Customer
from app.models.marketplace import SystemConfig, AnalyticsEvent, MarketingContent, ImportSession
from app.schemas.common import SuccessResponse
from app.core.auth import get_current_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    from decimal import Decimal

    total_products = await db.execute(select(func.count()).select_from(Product))
    total_orders = await db.execute(select(func.count()).select_from(Order))
    total_customers = await db.execute(select(func.count()).select_from(Customer))
    revenue_result = await db.execute(
        select(func.sum(Order.total)).where(Order.payment_status == "paid")
    )
    recent_orders = await db.execute(
        select(Order).order_by(Order.created_at.desc()).limit(5)
    )
    orders = recent_orders.scalars().all()

    return {
        "totals": {
            "products": total_products.scalar_one(),
            "orders": total_orders.scalar_one(),
            "customers": total_customers.scalar_one(),
            "revenue": float(revenue_result.scalar_one() or 0),
        },
        "recent_orders": [
            {
                "id": str(o.id),
                "order_number": o.order_number,
                "customer_name": o.customer_name,
                "total": float(o.total),
                "status": o.status,
                "created_at": str(o.created_at),
            }
            for o in orders
        ],
    }


@router.get("/analytics")
async def analytics_overview(
    period: str = Query(default="7d"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    interval_map = {"7d": "7 days", "30d": "30 days", "90d": "90 days"}
    interval = interval_map.get(period, "7 days")

    revenue = await db.execute(
        text(f"""
            SELECT DATE(created_at) as date, SUM(total) as revenue, COUNT(*) as orders
            FROM orders
            WHERE payment_status = 'paid'
              AND created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY DATE(created_at)
            ORDER BY date
        """)
    )
    by_channel = await db.execute(
        text(f"""
            SELECT channel, COUNT(*) as orders, SUM(total) as revenue
            FROM orders
            WHERE created_at >= NOW() - INTERVAL '{interval}'
            GROUP BY channel
        """)
    )

    return {
        "period": period,
        "revenue_by_day": [{"date": str(r[0]), "revenue": float(r[1] or 0), "orders": r[2]} for r in revenue],
        "by_channel": [{"channel": r[0], "orders": r[1], "revenue": float(r[2] or 0)} for r in by_channel],
    }


@router.get("/config")
async def get_config(db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.is_secret == False))
    configs = result.scalars().all()
    return {c.key: c.value_json or c.value for c in configs}


@router.post("/config/{key}")
async def set_config(key: str, value: str, db: AsyncSession = Depends(get_db), _=Depends(get_current_admin)):
    result = await db.execute(select(SystemConfig).where(SystemConfig.key == key))
    config = result.scalar_one_or_none()
    if config:
        config.value = value
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    await db.commit()
    return SuccessResponse(message=f"Config '{key}' updated")


@router.post("/ai/generate-listing/{product_id}")
async def generate_ai_listing(
    product_id: str,
    platform: str = Query(default="website"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    import uuid as uuid_module
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Product)
        .where(Product.id == uuid_module.UUID(product_id))
        .options(selectinload(Product.brand))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.services.ai_listing import generate_product_listing
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
        existing_description=product.description,
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
        if listing.get("seo_keywords"):
            product.seo_keywords = listing["seo_keywords"]
        product.ai_generated_listing = True
        await db.commit()

    return {"product_id": product_id, "platform": platform, "generated": listing}


@router.get("/import-sessions")
async def list_import_sessions(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_admin),
):
    result = await db.execute(
        select(ImportSession).order_by(ImportSession.created_at.desc()).limit(50)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "filename": s.filename,
            "source": s.source,
            "status": s.status,
            "total_rows": s.total_rows,
            "imported_count": s.imported_count,
            "updated_count": s.updated_count,
            "error_count": s.error_count,
            "created_at": str(s.created_at),
        }
        for s in sessions
    ]
