from __future__ import annotations

import uuid
from typing import Any, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_admin

log = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Optional model imports – gracefully degrade if models don't exist yet
# ---------------------------------------------------------------------------
try:
    from app.models.content import ProductEnrichment, ContentItem, TikTokContent
    _content_models_available = True
except ImportError:
    _content_models_available = False
    ProductEnrichment = None  # type: ignore[assignment,misc]
    ContentItem = None  # type: ignore[assignment,misc]
    TikTokContent = None  # type: ignore[assignment,misc]

try:
    from app.models.product import Product
    _product_model_available = True
except ImportError:
    _product_model_available = False
    Product = None  # type: ignore[assignment,misc]

# Optional enrichment service
try:
    from app.services.enrichment import generate_product_enrichment  # type: ignore[import]
    _enrichment_service_available = True
except ImportError:
    _enrichment_service_available = False
    generate_product_enrichment = None  # type: ignore[assignment]

# Optional TikTok / content generation service
try:
    from app.services.content_generation import (  # type: ignore[import]
        generate_tiktok_content,
        generate_content_item,
    )
    _content_service_available = True
except ImportError:
    _content_service_available = False
    generate_tiktok_content = None  # type: ignore[assignment]
    generate_content_item = None  # type: ignore[assignment]

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


def _require_content_models() -> None:
    if not _content_models_available:
        raise HTTPException(
            status_code=503,
            detail="Content models are not available. Run database migrations first.",
        )


def _require_product_model() -> None:
    if not _product_model_available:
        raise HTTPException(status_code=503, detail="Product model is not available.")


# ---------------------------------------------------------------------------
# Background helpers
# ---------------------------------------------------------------------------

async def _bulk_generate_enrichment(db_factory: Any) -> None:
    """Background task: generate enrichment for all products that lack it."""
    if not _content_models_available or not _product_model_available:
        log.warning("bulk_enrichment_skipped", reason="models_unavailable")
        return

    async with db_factory() as db:
        products_result = await db.execute(
            select(Product).where(Product.is_active == True)  # noqa: E712
        )
        all_products = products_result.scalars().all()

        for product in all_products:
            existing = await db.execute(
                select(ProductEnrichment).where(ProductEnrichment.product_id == product.id)
            )
            if existing.scalar_one_or_none():
                continue
            try:
                if _enrichment_service_available and generate_product_enrichment:
                    data = await generate_product_enrichment(product)
                else:
                    data = {}
                enrichment = ProductEnrichment(product_id=product.id, **data)
                db.add(enrichment)
                await db.commit()
            except Exception as exc:  # noqa: BLE001
                log.error("bulk_enrichment_item_failed", product_id=str(product.id), error=str(exc))
                await db.rollback()


# ---------------------------------------------------------------------------
# Enrichment endpoints
# ---------------------------------------------------------------------------

@router.post("/{product_id}/generate", dependencies=[Depends(get_current_admin)])
async def generate_enrichment(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate AI enrichment for a product and persist it."""
    _require_content_models()
    _require_product_model()

    # Fetch product
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Call enrichment service if available, otherwise produce stub
    if _enrichment_service_available and generate_product_enrichment:
        try:
            enrichment_data = await generate_product_enrichment(product)
        except Exception as exc:  # noqa: BLE001
            log.error("enrichment_generation_failed", product_id=str(product_id), error=str(exc))
            raise HTTPException(status_code=500, detail=f"Enrichment generation failed: {exc}") from exc
    else:
        enrichment_data = {}

    # Upsert ProductEnrichment
    existing_result = await db.execute(
        select(ProductEnrichment).where(ProductEnrichment.product_id == product_id)
    )
    enrichment = existing_result.scalar_one_or_none()
    if enrichment:
        for key, value in enrichment_data.items():
            setattr(enrichment, key, value)
    else:
        enrichment = ProductEnrichment(product_id=product_id, **enrichment_data)
        db.add(enrichment)

    # Backfill notes on the product if currently empty
    top_notes = enrichment_data.get("top_notes")
    middle_notes = enrichment_data.get("middle_notes")
    base_notes = enrichment_data.get("base_notes")
    if top_notes and not product.top_notes:
        product.top_notes = top_notes
    if middle_notes and not product.middle_notes:
        product.middle_notes = middle_notes
    if base_notes and not product.base_notes:
        product.base_notes = base_notes

    await db.commit()
    await db.refresh(enrichment)

    return {
        "id": str(enrichment.id),
        "product_id": str(enrichment.product_id),
        **{
            col: getattr(enrichment, col, None)
            for col in enrichment.__table__.columns.keys()  # type: ignore[union-attr]
            if col not in ("id", "product_id")
        },
    }


@router.get("/{product_id}", response_model=None)
async def get_enrichment(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return ProductEnrichment for a product."""
    _require_content_models()

    result = await db.execute(
        select(ProductEnrichment).where(ProductEnrichment.product_id == product_id)
    )
    enrichment = result.scalar_one_or_none()
    if not enrichment:
        raise HTTPException(status_code=404, detail="Enrichment not found for this product")

    return {
        "id": str(enrichment.id),
        "product_id": str(enrichment.product_id),
        **{
            col: getattr(enrichment, col, None)
            for col in enrichment.__table__.columns.keys()  # type: ignore[union-attr]
            if col not in ("id", "product_id")
        },
    }


@router.post("/bulk-generate", dependencies=[Depends(get_current_admin)])
async def bulk_generate_enrichment(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Queue a background task to generate enrichment for all products missing it."""
    _require_content_models()
    _require_product_model()

    count_result = await db.execute(select(Product).where(Product.is_active == True))  # noqa: E712
    products = count_result.scalars().all()

    # Filter to only those missing enrichment
    queued = 0
    for product in products:
        existing = await db.execute(
            select(ProductEnrichment).where(ProductEnrichment.product_id == product.id)
        )
        if not existing.scalar_one_or_none():
            queued += 1

    from app.database import AsyncSessionLocal  # type: ignore[import]
    background_tasks.add_task(_bulk_generate_enrichment, AsyncSessionLocal)

    return {
        "queued": queued,
        "message": f"Bulk enrichment started for {queued} product(s) missing enrichment data.",
    }


@router.get("/products/{product_id}/similar")
async def get_similar_products(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return similar products derived from enrichment data."""
    _require_content_models()
    _require_product_model()

    enrichment_result = await db.execute(
        select(ProductEnrichment).where(ProductEnrichment.product_id == product_id)
    )
    enrichment = enrichment_result.scalar_one_or_none()
    if not enrichment:
        raise HTTPException(status_code=404, detail="No enrichment data found for this product")

    # Expect enrichment to carry a `similar_product_ids` field (JSON list of UUIDs)
    similar_ids: list[str] = getattr(enrichment, "similar_product_ids", None) or []
    if not similar_ids:
        return []

    similar_uuids = []
    for raw_id in similar_ids:
        try:
            similar_uuids.append(uuid.UUID(str(raw_id)))
        except (ValueError, AttributeError):
            continue

    if not similar_uuids:
        return []

    products_result = await db.execute(
        select(Product).where(Product.id.in_(similar_uuids), Product.is_active == True)  # noqa: E712
    )
    products = products_result.scalars().all()

    return [
        {
            "id": str(p.id),
            "sku": p.sku,
            "name": p.name,
            "slug": p.slug,
            "brand_id": str(p.brand_id) if p.brand_id else None,
            "website_price": float(p.website_price) if p.website_price else None,
            "images": p.images,
            "fragrance_family": p.fragrance_family,
            "concentration": p.concentration,
            "gender": p.gender,
        }
        for p in products
    ]


# ---------------------------------------------------------------------------
# TikTok content endpoints
# ---------------------------------------------------------------------------

@router.post("/tiktok/{product_id}/generate", dependencies=[Depends(get_current_admin)])
async def generate_tiktok(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate TikTok content for a product and save to database."""
    _require_content_models()
    _require_product_model()

    product_result = await db.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if _content_service_available and generate_tiktok_content:
        try:
            tiktok_data = await generate_tiktok_content(product)
        except Exception as exc:  # noqa: BLE001
            log.error("tiktok_generation_failed", product_id=str(product_id), error=str(exc))
            raise HTTPException(status_code=500, detail=f"TikTok content generation failed: {exc}") from exc
    else:
        tiktok_data = {
            "script": "",
            "hashtags": [],
            "hook": "",
            "cta": "",
        }

    content = TikTokContent(product_id=product_id, **tiktok_data)
    db.add(content)
    await db.commit()
    await db.refresh(content)

    return {
        "id": str(content.id),
        "product_id": str(content.product_id),
        **{
            col: getattr(content, col, None)
            for col in content.__table__.columns.keys()  # type: ignore[union-attr]
            if col not in ("id", "product_id")
        },
    }


@router.get("/tiktok/{product_id}", dependencies=[Depends(get_current_admin)])
async def get_tiktok_content(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return all TikTok content entries for a product."""
    _require_content_models()

    result = await db.execute(
        select(TikTokContent)
        .where(TikTokContent.product_id == product_id)
        .order_by(TikTokContent.created_at.desc())  # type: ignore[union-attr]
    )
    items = result.scalars().all()
    return [
        {
            "id": str(item.id),
            "product_id": str(item.product_id),
            **{
                col: getattr(item, col, None)
                for col in item.__table__.columns.keys()  # type: ignore[union-attr]
                if col not in ("id", "product_id")
            },
        }
        for item in items
    ]


# ---------------------------------------------------------------------------
# Generic content endpoints
# ---------------------------------------------------------------------------

@router.post("/content/generate", dependencies=[Depends(get_current_admin)])
async def generate_content(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Generate and save a ContentItem.

    Expected body: ``{"content_type": str, "params": dict}``
    """
    _require_content_models()

    content_type: str = payload.get("content_type", "")
    params: dict[str, Any] = payload.get("params", {})

    if not content_type:
        raise HTTPException(status_code=422, detail="`content_type` is required")

    if _content_service_available and generate_content_item:
        try:
            content_data = await generate_content_item(content_type=content_type, params=params)
        except Exception as exc:  # noqa: BLE001
            log.error("content_generation_failed", content_type=content_type, error=str(exc))
            raise HTTPException(status_code=500, detail=f"Content generation failed: {exc}") from exc
    else:
        content_data = {"body": "", "status": "draft"}

    content_item = ContentItem(content_type=content_type, **content_data)
    db.add(content_item)
    await db.commit()
    await db.refresh(content_item)

    return {
        "id": str(content_item.id),
        "content_type": content_item.content_type,
        **{
            col: getattr(content_item, col, None)
            for col in content_item.__table__.columns.keys()  # type: ignore[union-attr]
            if col not in ("id", "content_type")
        },
    }


@router.get("/content")
async def list_content(
    content_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List ContentItems with optional filters."""
    _require_content_models()

    query = select(ContentItem)
    if content_type:
        query = query.where(ContentItem.content_type == content_type)
    if status:
        query = query.where(ContentItem.status == status)
    query = query.order_by(ContentItem.created_at.desc()).limit(limit)  # type: ignore[union-attr]

    result = await db.execute(query)
    items = result.scalars().all()

    return [
        {
            "id": str(item.id),
            "content_type": item.content_type,
            **{
                col: getattr(item, col, None)
                for col in item.__table__.columns.keys()  # type: ignore[union-attr]
                if col not in ("id", "content_type")
            },
        }
        for item in items
    ]


@router.get("/content/{slug}")
async def get_content_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return a single ContentItem by slug and increment its view count."""
    _require_content_models()

    result = await db.execute(select(ContentItem).where(ContentItem.slug == slug))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    # Increment view_count if the column exists
    if hasattr(item, "view_count"):
        item.view_count = (item.view_count or 0) + 1
        await db.commit()
        await db.refresh(item)

    return {
        "id": str(item.id),
        "content_type": item.content_type,
        **{
            col: getattr(item, col, None)
            for col in item.__table__.columns.keys()  # type: ignore[union-attr]
            if col not in ("id", "content_type")
        },
    }
