"""Recommendation engine: similar products, frequently-bought-together,
complete-the-look (cross-category), trending, and best sellers.

All functions return lists of Product ORM objects (brand eager-loaded) so the
router can serialize them with the standard ProductListItem schema.
"""
from __future__ import annotations
import uuid
from typing import Optional

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, Category
from app.models.order import OrderItem

# Which categories pair well with each schema type for "complete the look".
COMPLEMENTARY = {
    "sneakers": ["streetwear", "accessories", "fragrances"],
    "clothing": ["sneakers", "accessories", "fragrances"],
    "bags": ["accessories", "fragrances", "jewelry"],
    "fragrance": ["fragrances"],
    "accessories": ["bags", "watches", "fragrances"],
    "watches": ["accessories", "jewelry", "fragrances"],
    "jewelry": ["watches", "bags", "fragrances"],
}


def _base_active_query():
    return select(Product).where(Product.is_active == True).options(  # noqa: E712
        selectinload(Product.brand)
    )


async def similar_products(db: AsyncSession, product: Product, limit: int = 8) -> list[Product]:
    """Products in the same category, preferring same brand / shared attributes."""
    query = _base_active_query().where(Product.id != product.id)
    if product.category_id:
        query = query.where(Product.category_id == product.category_id)
    # Prefer same brand, then featured/highly rated.
    query = query.order_by(
        (Product.brand_id == product.brand_id).desc() if product.brand_id else Product.is_featured.desc(),
        Product.is_featured.desc(),
        Product.order_count.desc(),
    ).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def frequently_bought_together(db: AsyncSession, product_id: uuid.UUID, limit: int = 4) -> list[Product]:
    """Products most often appearing in the same orders as the given product."""
    # Orders containing the seed product.
    seed_orders = select(OrderItem.order_id).where(OrderItem.product_id == product_id).subquery()
    # Co-occurring products ranked by co-purchase count.
    cooccur = (
        select(OrderItem.product_id, func.count().label("freq"))
        .where(
            OrderItem.order_id.in_(select(seed_orders.c.order_id)),
            OrderItem.product_id != product_id,
            OrderItem.product_id.isnot(None),
        )
        .group_by(OrderItem.product_id)
        .order_by(func.count().desc())
        .limit(limit)
    )
    rows = (await db.execute(cooccur)).all()
    product_ids = [r[0] for r in rows]
    if not product_ids:
        return []
    result = await db.execute(_base_active_query().where(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}
    return [products[pid] for pid in product_ids if pid in products]


async def complete_the_look(db: AsyncSession, product: Product, limit: int = 6) -> list[Product]:
    """Cross-category recommendations (e.g. sneakers → streetwear + accessories)."""
    schema_type = None
    if product.category_id:
        cat = await db.get(Category, product.category_id)
        schema_type = cat.attribute_schema_type if cat else None
    target_slugs = COMPLEMENTARY.get(schema_type or "", ["fragrances", "accessories"])

    cat_ids_result = await db.execute(
        select(Category.id).where(Category.slug.in_(target_slugs))
    )
    cat_ids = [c[0] for c in cat_ids_result.all()]
    if not cat_ids:
        return []
    query = (
        _base_active_query()
        .where(Product.category_id.in_(cat_ids), Product.id != product.id)
        .order_by(Product.is_featured.desc(), Product.order_count.desc(), func.random())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def trending(db: AsyncSession, limit: int = 12, category_slug: Optional[str] = None) -> list[Product]:
    """Trending = recent demand signal via view_count + order_count."""
    query = _base_active_query()
    if category_slug:
        query = query.where(Product.category_id == select(Category.id).where(Category.slug == category_slug).scalar_subquery())
    query = query.order_by((Product.order_count * 3 + Product.view_count).desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def bestsellers(db: AsyncSession, limit: int = 12, category_slug: Optional[str] = None) -> list[Product]:
    query = _base_active_query().where(Product.order_count > 0)
    if category_slug:
        query = query.where(Product.category_id == select(Category.id).where(Category.slug == category_slug).scalar_subquery())
    query = query.order_by(Product.order_count.desc(), Product.revenue_total.desc()).limit(limit)
    result = await db.execute(query)
    products = list(result.scalars().all())
    # Fall back to featured if there's no sales history yet (cold start).
    if not products:
        fb = _base_active_query().order_by(Product.is_featured.desc(), Product.created_at.desc()).limit(limit)
        products = list((await db.execute(fb)).scalars().all())
    return products
