"""Conversion engine endpoints: recommendations + AI shopping assistant."""
from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductListItem
from app.services import recommendations as rec
from app.services.shopping_assistant import recommend as assistant_recommend

router = APIRouter(prefix="/recommendations", tags=["recommendations"])
assistant_router = APIRouter(prefix="/assistant", tags=["assistant"])


def _serialize(products) -> list[dict]:
    return [ProductListItem.model_validate(p).model_dump(mode="json") for p in products]


async def _load_product(db: AsyncSession, product_id: uuid.UUID) -> Product:
    result = await db.execute(
        select(Product).where(Product.id == product_id).options(selectinload(Product.brand))
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/similar/{product_id}")
async def get_similar(product_id: uuid.UUID, limit: int = Query(8, le=24), db: AsyncSession = Depends(get_db)):
    product = await _load_product(db, product_id)
    return {"items": _serialize(await rec.similar_products(db, product, limit))}


@router.get("/frequently-bought-together/{product_id}")
async def get_fbt(product_id: uuid.UUID, limit: int = Query(4, le=12), db: AsyncSession = Depends(get_db)):
    return {"items": _serialize(await rec.frequently_bought_together(db, product_id, limit))}


@router.get("/complete-the-look/{product_id}")
async def get_complete_the_look(product_id: uuid.UUID, limit: int = Query(6, le=18), db: AsyncSession = Depends(get_db)):
    product = await _load_product(db, product_id)
    return {"items": _serialize(await rec.complete_the_look(db, product, limit))}


@router.get("/trending")
async def get_trending(limit: int = Query(12, le=48), category_slug: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return {"items": _serialize(await rec.trending(db, limit, category_slug))}


@router.get("/bestsellers")
async def get_bestsellers(limit: int = Query(12, le=48), category_slug: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return {"items": _serialize(await rec.bestsellers(db, limit, category_slug))}


class RecentlyViewedRequest(BaseModel):
    product_ids: list[uuid.UUID]


@router.post("/recently-viewed")
async def get_recently_viewed(payload: RecentlyViewedRequest, db: AsyncSession = Depends(get_db)):
    """Hydrate a client-held list of recently-viewed product IDs into full products."""
    if not payload.product_ids:
        return {"items": []}
    result = await db.execute(
        select(Product).where(Product.id.in_(payload.product_ids), Product.is_active == True)  # noqa: E712
        .options(selectinload(Product.brand))
    )
    by_id = {p.id: p for p in result.scalars().all()}
    ordered = [by_id[pid] for pid in payload.product_ids if pid in by_id]
    return {"items": _serialize(ordered)}


class AssistantRequest(BaseModel):
    query: str
    limit: int = 12


@assistant_router.post("/recommend")
async def assistant(payload: AssistantRequest, db: AsyncSession = Depends(get_db)):
    """Natural-language shopping: 'find me an outfit for a car meet under $300'."""
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query is required")
    result = await assistant_recommend(db, payload.query.strip(), min(payload.limit, 24))
    return {
        "message": result["message"],
        "intent": result["intent"],
        "items": _serialize(result["products"]),
    }
