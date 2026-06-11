"""Product media upload: normalize → R2 → CDN URL persisted on the product."""
from __future__ import annotations
import io
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.config import settings
from app.core.auth import get_current_admin
from app.database import get_db
from app.models.product import Product
from app.services.media import InvalidImageError, normalize_image
from app.services import storage

router = APIRouter(prefix="/upload", tags=["upload"], dependencies=[Depends(get_current_admin)])


@router.post("/product-image")
async def upload_product_image(
    file: UploadFile = File(...),
    product_id: Optional[uuid.UUID] = None,
    is_primary: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Upload one product image.

    The image is validated, normalized (resize/compress/strip metadata),
    stored in Cloudflare R2, and — when `product_id` is given — appended to
    the product's image list so it flows to the storefront and marketplaces.
    """
    if not settings.R2_CONFIGURED:
        raise HTTPException(status_code=503, detail="Media storage (R2) is not configured")

    raw = await file.read()
    try:
        normalized = normalize_image(raw)
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    url = storage.upload_file(
        io.BytesIO(normalized.data),
        filename=f"upload{normalized.extension}",
        content_type=normalized.content_type,
        folder="products",
    )

    image_entry = {
        "url": url,
        "width": normalized.width,
        "height": normalized.height,
        "is_primary": is_primary,
    }

    if product_id:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        images = list(product.images or [])
        if is_primary:
            for img in images:
                if isinstance(img, dict):
                    img["is_primary"] = False
            images.insert(0, image_entry)
        else:
            images.append(image_entry)
        product.images = images
        flag_modified(product, "images")
        await db.commit()

    return {
        "url": url,
        "width": normalized.width,
        "height": normalized.height,
        "content_type": normalized.content_type,
        "bytes": len(normalized.data),
        "attached_to_product": str(product_id) if product_id else None,
    }
