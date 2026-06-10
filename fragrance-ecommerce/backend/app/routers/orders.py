from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderListItem, OrderFilter
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.core.auth import get_current_user, get_current_admin
from app.core.dependencies import get_pagination
from app.services.order_processor import create_order, update_order_status

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
async def place_order(payload: OrderCreate, db: AsyncSession = Depends(get_db)):
    order = await create_order(db, payload)
    await db.commit()
    await db.refresh(order, ["items"])
    return order


@router.get("", response_model=PaginatedResponse[OrderListItem], dependencies=[Depends(get_current_admin)])
async def list_orders(
    search: str = Query(default=None),
    status: str = Query(default=None),
    payment_status: str = Query(default=None),
    channel: str = Query(default=None),
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order)
    if search:
        query = query.where(or_(
            Order.order_number.ilike(f"%{search}%"),
            Order.guest_email.ilike(f"%{search}%"),
            Order.customer_name.ilike(f"%{search}%"),
        ))
    if status:
        query = query.where(Order.status == status)
    if payment_status:
        query = query.where(Order.payment_status == payment_status)
    if channel:
        query = query.where(Order.channel == channel)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()

    query = query.order_by(Order.created_at.desc()).offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query.options(selectinload(Order.items)))
    items = result.scalars().all()

    list_items = []
    for o in items:
        list_items.append(OrderListItem(
            id=o.id,
            order_number=o.order_number,
            customer_id=o.customer_id,
            customer_name=o.customer_name,
            channel=o.channel,
            status=o.status,
            payment_status=o.payment_status,
            fulfillment_status=o.fulfillment_status,
            total=o.total,
            currency=o.currency,
            item_count=len(o.items),
        ))

    return PaginatedResponse.create(list_items, total, pagination.page, pagination.page_size)


@router.get("/my", response_model=PaginatedResponse[OrderListItem])
async def my_orders(
    pagination: PaginationParams = Depends(get_pagination),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Order).where(Order.customer_id == current_user.id).order_by(Order.created_at.desc())
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar_one()
    query = query.offset(pagination.offset).limit(pagination.page_size)
    result = await db.execute(query.options(selectinload(Order.items)))
    items = result.scalars().all()
    list_items = [
        OrderListItem(
            id=o.id, order_number=o.order_number, customer_id=o.customer_id,
            customer_name=o.customer_name, channel=o.channel, status=o.status,
            payment_status=o.payment_status, fulfillment_status=o.fulfillment_status,
            total=o.total, currency=o.currency, item_count=len(o.items),
        )
        for o in items
    ]
    return PaginatedResponse.create(list_items, total, pagination.page, pagination.page_size)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse, dependencies=[Depends(get_current_admin)])
async def update_order(order_id: uuid.UUID, payload: OrderUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(order, k, v)
    await db.commit()
    await db.refresh(order)
    return order


# ---------------------------------------------------------------------------
# Fulfillment (admin)
# ---------------------------------------------------------------------------
from pydantic import BaseModel  # noqa: E402
from app.services.fulfillment import process_paid_order, assign_tracking  # noqa: E402


class TrackingRequest(BaseModel):
    tracking_number: str
    carrier: str | None = None
    tracking_url: str | None = None


@router.get("/fulfillment/queue", response_model=PaginatedResponse[OrderListItem], dependencies=[Depends(get_current_admin)])
async def fulfillment_queue(
    pagination: PaginationParams = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    """Paid orders awaiting fulfillment or tracking."""
    base = select(Order).where(
        Order.payment_status == "paid",
        Order.fulfillment_status.in_(["unfulfilled", "processing"]),
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = await db.execute(
        base.order_by(Order.created_at.asc()).offset(pagination.offset).limit(pagination.page_size)
    )
    return PaginatedResponse.create(rows.scalars().all(), total, pagination.page, pagination.page_size)


@router.post("/{order_id}/fulfill", dependencies=[Depends(get_current_admin)])
async def run_fulfillment(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id)
        .options(selectinload(Order.items), selectinload(Order.customer))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await process_paid_order(db, order)


@router.post("/{order_id}/tracking", dependencies=[Depends(get_current_admin)])
async def set_tracking(order_id: uuid.UUID, payload: TrackingRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Order).where(Order.id == order_id)
        .options(selectinload(Order.items), selectinload(Order.customer))
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return await assign_tracking(db, order, payload.tracking_number, payload.carrier, payload.tracking_url)
