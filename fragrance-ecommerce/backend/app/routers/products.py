from __future__ import annotations
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.product import Brand, Category, Product, ProductVariant, Collection, CollectionProduct
from app.schemas.product import (
    BrandCreate, BrandUpdate, BrandResponse,
    CategoryCreate, CategoryResponse,
    ProductCreate, ProductUpdate, ProductResponse, ProductListItem, ProductFilter,
    CollectionCreate, CollectionUpdate, CollectionResponse,
)
from app.schemas.common import PaginatedResponse, PaginationParams, SortParams, SuccessResponse
from app.core.auth import get_current_admin
from app.core.dependencies import get_pagination, get_sort

router = APIRouter(prefix="/products", tags=["products"])
brands_router = APIRouter(prefix="/brands", tags=["brands"])
categories_router = APIRouter(prefix="/categories", tags=["categories"])
collections_router = APIRouter(prefix="/collections", tags=["collections"])


@brands_router.get("", response_model=List[BrandResponse])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).where(Brand.is_active == True).order_by(Brand.name))
    return result.scalars().all()


@brands_router.post("", response_model=BrandResponse, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_brand(payload: BrandCreate, db: AsyncSession = Depends(get_db)):
    brand = Brand(**payload.model_dump())
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@brands_router.patch("/{brand_id}", response_model=BrandResponse, dependencies=[Depends(get_current_admin)])
async def update_brand(brand_id: uuid.UUID, payload: BrandUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(brand, k, v)
    await db.commit()
    await db.refresh(brand)
    return brand


@categories_router.get("", response_model=List[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Category)
        .where(Category.is_active == True, Category.parent_id == None)
        .order_by(Category.sort_order)
        .options(selectinload(Category.children))
    )
    return result.scalars().all()


@categories_router.post("", response_model=CategoryResponse, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = Category(**payload.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.get("", response_model=PaginatedResponse[ProductListItem])
async def list_products(
    search: Optional[str] = Query(default=None),
    brand_id: Optional[uuid.UUID] = Query(default=None),
    category_id: Optional[uuid.UUID] = Query(default=None),
    gender: Optional[str] = Query(default=None),
    concentration: Optional[str] = Query(default=None),
    is_featured: Optional[bool] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    max_price: Optional[float] = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    sort: SortParams = Depends(get_sort),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Product)
        .where(Product.is_active == True)
        .options(selectinload(Product.brand), selectinload(Product.variants))
    )
    if search:
        query = query.where(or_(
            Product.name.ilike(f"%{search}%"),
            Product.sku.ilike(f"%{search}%"),
        ))
    if brand_id:
        query = query.where(Product.brand_id == brand_id)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if gender:
        query = query.where(Product.gender == gender)
    if concentration:
        query = query.where(Product.concentration == concentration)
    if is_featured is not None:
        query = query.where(Product.is_featured == is_featured)
    if min_price is not None:
        query = query.where(Product.website_price >= min_price)
    if max_price is not None:
        query = query.where(Product.website_price <= max_price)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    sort_col = getattr(Product, sort.sort_by, Product.created_at) if sort.sort_by else Product.created_at
    query = query.order_by(sort_col.desc() if sort.sort_dir == "desc" else sort_col.asc())
    query = query.offset(pagination.offset).limit(pagination.page_size)

    result = await db.execute(query)
    items = result.scalars().all()
    return PaginatedResponse.create(items, total, pagination.page, pagination.page_size)


@router.get("/{slug}", response_model=ProductResponse)
async def get_product(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product)
        .where(Product.slug == slug)
        .options(selectinload(Product.brand), selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.view_count = (product.view_count or 0) + 1
    await db.commit()
    return product


@router.post("", response_model=ProductResponse, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    data = payload.model_dump(exclude={"variants"})
    variants_data = payload.variants
    product = Product(**data)
    for v in variants_data:
        product.variants.append(ProductVariant(**v.model_dump()))
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductResponse, dependencies=[Depends(get_current_admin)])
async def update_product(product_id: uuid.UUID, payload: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.brand), selectinload(Product.variants))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", dependencies=[Depends(get_current_admin)])
async def delete_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()
    return SuccessResponse(message="Product deleted")


@collections_router.get("", response_model=List[CollectionResponse])
async def list_collections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Collection).where(Collection.is_active == True).order_by(Collection.sort_order)
    )
    return result.scalars().all()


@collections_router.post("", response_model=CollectionResponse, status_code=201, dependencies=[Depends(get_current_admin)])
async def create_collection(payload: CollectionCreate, db: AsyncSession = Depends(get_db)):
    col = Collection(**payload.model_dump())
    db.add(col)
    await db.commit()
    await db.refresh(col)
    return col


@collections_router.get("/{slug}", response_model=CollectionResponse)
async def get_collection(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Collection).where(Collection.slug == slug))
    col = result.scalar_one_or_none()
    if not col:
        raise HTTPException(status_code=404, detail="Collection not found")
    return col
