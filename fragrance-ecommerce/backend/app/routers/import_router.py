from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.marketplace import ImportSession
from app.models.product import Brand, Product, Supplier
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.core.auth import get_current_admin, get_current_user
from app.core.dependencies import get_pagination
from app.services.product_import import parse_spreadsheet
from app.services.seo import slugify

router = APIRouter(prefix="/import", tags=["import"])


async def _get_or_create_brand(db: AsyncSession, brand_name: str) -> Brand:
    slug = slugify(brand_name)
    result = await db.execute(select(Brand).where(Brand.slug == slug))
    brand = result.scalar_one_or_none()
    if not brand:
        brand = Brand(name=brand_name, slug=slug)
        db.add(brand)
        await db.flush()
    return brand


@router.post("/upload")
async def upload_spreadsheet(
    file: UploadFile = File(...),
    supplier_id: Optional[uuid.UUID] = Form(default=None),
    source: str = Form(default="manual"),
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed = {".csv", ".xlsx", ".xls"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {', '.join(allowed)}")

    content = await file.read()

    session = ImportSession(
        filename=file.filename,
        source=source,
        status="processing",
        initiated_by=current_user.id,
    )
    db.add(session)
    await db.flush()

    try:
        products_data, errors = parse_spreadsheet(content, file.filename, supplier_id)
        session.total_rows = len(products_data) + len(errors)
        session.error_count = len(errors)
        session.errors = errors

        imported = 0
        updated = 0
        skipped = 0

        brand_cache: dict[str, Brand] = {}

        for p_data in products_data:
            brand_name = p_data.pop("brand_name", None)
            if brand_name:
                if brand_name not in brand_cache:
                    brand_cache[brand_name] = await _get_or_create_brand(db, brand_name)
                p_data["brand_id"] = brand_cache[brand_name].id

            existing = await db.execute(select(Product).where(Product.sku == p_data["sku"]))
            existing_product = existing.scalar_one_or_none()

            if not existing_product:
                slug = p_data.get("slug", "")
                slug_check = await db.execute(select(Product).where(Product.slug == slug))
                if slug_check.scalar_one_or_none():
                    p_data["slug"] = f"{slug}-{uuid.uuid4().hex[:6]}"

                product = Product(**{k: v for k, v in p_data.items() if v is not None})
                db.add(product)
                imported += 1
            else:
                for k, v in p_data.items():
                    if v is not None and k not in ("sku", "slug"):
                        setattr(existing_product, k, v)
                updated += 1

            session.processed_rows += 1

        session.imported_count = imported
        session.updated_count = updated
        session.skipped_count = skipped
        session.status = "completed"

        await db.commit()

        return {
            "session_id": str(session.id),
            "status": "completed",
            "total_rows": session.total_rows,
            "imported": imported,
            "updated": updated,
            "skipped": skipped,
            "errors": len(errors),
            "error_details": errors[:20],
        }

    except Exception as e:
        session.status = "failed"
        session.errors = [str(e)]
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/sessions", dependencies=[Depends(get_current_admin)])
async def list_import_sessions(
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import func
    query = select(ImportSession).order_by(ImportSession.created_at.desc())
    count = await db.execute(select(func.count()).select_from(ImportSession))
    total = count.scalar_one()
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query)
    items = result.scalars().all()
    return PaginatedResponse.create(
        [{"id": str(s.id), "filename": s.filename, "source": s.source, "status": s.status,
          "imported_count": s.imported_count, "updated_count": s.updated_count,
          "error_count": s.error_count, "created_at": str(s.created_at)} for s in items],
        total, pagination.page, pagination.page_size,
    )
