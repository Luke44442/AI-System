from __future__ import annotations
import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.marketplace import MarketplaceListing, DiscountCode, Review
from app.models.product import Product
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.core.auth import get_current_admin
from app.core.dependencies import get_pagination

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


# ---------------------------------------------------------------------------
# Marketplace sync + monitoring (admin)
# ---------------------------------------------------------------------------
@router.get("/status", dependencies=[Depends(get_current_admin)])
async def marketplace_status(db: AsyncSession = Depends(get_db)):
    """Per-platform configuration, capabilities, listing counts, and failures."""
    from app.services.marketplaces.service import sync_health
    return await sync_health(db)


@router.post("/sync/{product_id}", dependencies=[Depends(get_current_admin)])
async def sync_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Post/update a single product across all configured marketplaces now."""
    from app.services.marketplaces.service import sync_product_all
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.brand))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"product_id": str(product_id), "results": await sync_product_all(db, product)}


@router.post("/sync-all", dependencies=[Depends(get_current_admin)])
async def sync_all(db: AsyncSession = Depends(get_db)):
    """Trigger a full catalog sync to all configured marketplaces (runs inline)."""
    from app.services.marketplaces.service import sync_all_active_products
    return await sync_all_active_products(db)


@router.get("/listings", dependencies=[Depends(get_current_admin)])
async def list_listings(
    platform: str = Query(default=None),
    status: str = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    query = select(MarketplaceListing)
    if platform:
        query = query.where(MarketplaceListing.platform == platform)
    if status:
        query = query.where(MarketplaceListing.status == status)
    count = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count.scalar_one()
    query = query.order_by(MarketplaceListing.created_at.desc()).offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    return PaginatedResponse.create(
        [{"id": str(l.id), "product_id": str(l.product_id), "platform": l.platform,
          "listing_id": l.listing_id, "status": l.status, "price": str(l.price) if l.price else None,
          "listing_url": l.listing_url, "last_synced_at": l.last_synced_at} for l in items],
        total, pagination.page, pagination.page_size,
    )


class UpdateListingRequest(BaseModel):
    status: Optional[str] = None
    listing_id: Optional[str] = None
    listing_url: Optional[str] = None
    price: Optional[Decimal] = None
    title: Optional[str] = None
    description: Optional[str] = None


@router.patch("/listings/{listing_id}", dependencies=[Depends(get_current_admin)])
async def update_listing(listing_id: uuid.UUID, payload: UpdateListingRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MarketplaceListing).where(MarketplaceListing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(listing, k, v)
    await db.commit()
    return SuccessResponse(message="Listing updated")


@router.get("/discount-codes", dependencies=[Depends(get_current_admin)])
async def list_discount_codes(
    is_active: bool = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    query = select(DiscountCode)
    if is_active is not None:
        query = query.where(DiscountCode.is_active == is_active)
    count = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count.scalar_one()
    result = await db.execute(query.order_by(DiscountCode.created_at.desc()).offset(pagination.offset).limit(pagination.page_size))
    items = result.scalars().all()
    return PaginatedResponse.create(
        [{"id": str(d.id), "code": d.code, "discount_type": d.discount_type,
          "discount_value": str(d.discount_value), "usage_count": d.usage_count,
          "is_active": d.is_active, "expires_at": d.expires_at} for d in items],
        total, pagination.page, pagination.page_size,
    )


@router.post("/discount-codes/validate")
async def validate_discount(code: str, order_total: float, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiscountCode).where(DiscountCode.code == code.upper(), DiscountCode.is_active == True))
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Invalid or expired discount code")
    if discount.usage_limit and discount.usage_count >= discount.usage_limit:
        raise HTTPException(status_code=400, detail="Discount code usage limit reached")
    if discount.min_order_amount and order_total < float(discount.min_order_amount):
        raise HTTPException(status_code=400, detail=f"Minimum order amount is ${discount.min_order_amount}")
    from decimal import Decimal
    if discount.discount_type == "percentage":
        amount = Decimal(str(order_total)) * discount.discount_value / 100
    else:
        amount = discount.discount_value
    if discount.max_discount_amount:
        amount = min(amount, discount.max_discount_amount)
    return {"valid": True, "discount_amount": float(amount), "discount_type": discount.discount_type}


@router.get("/reviews")
async def list_reviews(
    product_id: uuid.UUID = Query(default=None),
    is_approved: bool = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    query = select(Review)
    if product_id:
        query = query.where(Review.product_id == product_id)
    if is_approved is not None:
        query = query.where(Review.is_approved == is_approved)
    count = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count.scalar_one()
    result = await db.execute(query.order_by(Review.created_at.desc()).offset(pagination.offset).limit(pagination.page_size))
    items = result.scalars().all()
    return PaginatedResponse.create(
        [{"id": str(r.id), "product_id": str(r.product_id), "rating": r.rating,
          "title": r.title, "body": r.body, "reviewer_name": r.reviewer_name,
          "is_verified_purchase": r.is_verified_purchase, "is_approved": r.is_approved,
          "created_at": str(r.created_at)} for r in items],
        total, pagination.page, pagination.page_size,
    )


@router.patch("/reviews/{review_id}/approve", dependencies=[Depends(get_current_admin)])
async def approve_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Review).where(Review.id == review_id))
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.is_approved = True
    await db.commit()
    return SuccessResponse(message="Review approved")
