from __future__ import annotations
import uuid
from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.auth import get_current_admin
from app.models.analytics import OrderProfitability, SupplierCostHistory, KeywordRanking, CompetitorPrice, PricingAlert
from app.models.order import Order
from app.models.product import Product
import structlog

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class CompetitorPriceCreate(BaseModel):
    product_id: uuid.UUID
    competitor_name: str
    competitor_url: Optional[str] = None
    competitor_price: float


class KeywordCreate(BaseModel):
    keyword: str
    target_url: str
    product_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    rank: int
    search_volume: Optional[int] = None
    difficulty_score: Optional[float] = None


@router.get("/profitability", dependencies=[Depends(get_current_admin)])
async def get_profitability(
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    channel: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(OrderProfitability, Order.order_number, Order.created_at)
        .join(Order, Order.id == OrderProfitability.order_id)
        .order_by(Order.created_at.desc())
    )
    if channel:
        query = query.where(OrderProfitability.channel == channel)
    if from_date:
        query = query.where(Order.created_at >= from_date)
    if to_date:
        query = query.where(Order.created_at <= to_date)
    query = query.limit(limit)

    result = await db.execute(query)
    rows = result.all()

    items = []
    total_revenue = Decimal("0")
    total_profit = Decimal("0")
    channel_data: dict = {}

    for prof, order_num, created_at in rows:
        total_revenue += prof.revenue or Decimal("0")
        total_profit += prof.net_profit or Decimal("0")
        ch = prof.channel or "website"
        if ch not in channel_data:
            channel_data[ch] = {"revenue": Decimal("0"), "profit": Decimal("0"), "orders": 0}
        channel_data[ch]["revenue"] += prof.revenue or Decimal("0")
        channel_data[ch]["profit"] += prof.net_profit or Decimal("0")
        channel_data[ch]["orders"] += 1
        items.append({
            "order_id": str(prof.order_id),
            "order_number": order_num,
            "order_date": created_at.isoformat() if created_at else None,
            "revenue": float(prof.revenue or 0),
            "supplier_cost": float(prof.supplier_cost or 0),
            "shipping_cost": float(prof.shipping_cost or 0),
            "platform_fee": float(prof.platform_fee or 0),
            "stripe_fee": float(prof.stripe_fee or 0),
            "gross_profit": float(prof.gross_profit or 0),
            "net_profit": float(prof.net_profit or 0),
            "margin_pct": float(prof.margin_pct or 0),
            "channel": prof.channel,
        })

    avg_margin = float(total_profit / total_revenue * 100) if total_revenue else 0

    return {
        "items": items,
        "summary": {
            "total_revenue": float(total_revenue),
            "total_profit": float(total_profit),
            "avg_margin_pct": round(avg_margin, 2),
            "by_channel": {
                k: {
                    "revenue": float(v["revenue"]),
                    "profit": float(v["profit"]),
                    "orders": v["orders"],
                }
                for k, v in channel_data.items()
            },
        },
    }


@router.post("/profitability/calculate/{order_id}", dependencies=[Depends(get_current_admin)])
async def calculate_order_profitability(order_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    from app.services.pricing_intelligence import calculate_order_profitability

    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    existing = await db.execute(select(OrderProfitability).where(OrderProfitability.order_id == order_id))
    prof = existing.scalar_one_or_none()

    data = calculate_order_profitability(
        order_total=order.total,
        supplier_cost=order.supplier_cost_total,
        shipping_cost=order.shipping_amount,
        channel=order.channel,
    )

    if prof:
        for k, v in data.items():
            setattr(prof, k, v)
        prof.channel = order.channel
    else:
        prof = OrderProfitability(order_id=order.id, channel=order.channel, **data)
        db.add(prof)

    await db.commit()
    return {"order_id": str(order_id), **{k: float(v) for k, v in data.items()}}


@router.get("/supplier-costs/{product_id}", dependencies=[Depends(get_current_admin)])
async def get_supplier_cost_history(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SupplierCostHistory)
        .where(SupplierCostHistory.product_id == product_id)
        .order_by(SupplierCostHistory.changed_at.desc())
        .limit(100)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "old_cost": float(r.old_cost),
            "new_cost": float(r.new_cost),
            "change_pct": float(r.change_pct),
            "source": r.source,
            "notes": r.notes,
            "changed_at": r.changed_at.isoformat() if r.changed_at else None,
        }
        for r in rows
    ]


@router.post("/competitor-prices", dependencies=[Depends(get_current_admin)])
async def add_competitor_price(payload: CompetitorPriceCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == payload.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    our_price = float(product.website_price or 0)
    comp_price = payload.competitor_price
    price_diff = our_price - comp_price
    price_diff_pct = (price_diff / comp_price * 100) if comp_price else 0

    entry = CompetitorPrice(
        product_id=payload.product_id,
        competitor_name=payload.competitor_name,
        competitor_url=payload.competitor_url,
        competitor_price=Decimal(str(comp_price)),
        our_price=Decimal(str(our_price)),
        price_diff=Decimal(str(round(price_diff, 2))),
        price_diff_pct=Decimal(str(round(price_diff_pct, 2))),
        we_are_cheaper=price_diff < 0,
        is_active=True,
    )
    db.add(entry)
    await db.commit()
    return {
        "competitor_name": entry.competitor_name,
        "competitor_price": float(entry.competitor_price),
        "our_price": float(entry.our_price),
        "price_diff": float(entry.price_diff),
        "price_diff_pct": float(entry.price_diff_pct),
        "we_are_cheaper": entry.we_are_cheaper,
    }


@router.get("/competitor-prices/{product_id}", dependencies=[Depends(get_current_admin)])
async def get_competitor_prices(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CompetitorPrice)
        .where(CompetitorPrice.product_id == product_id, CompetitorPrice.is_active == True)
        .order_by(CompetitorPrice.tracked_at.desc())
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "competitor_name": r.competitor_name,
            "competitor_url": r.competitor_url,
            "competitor_price": float(r.competitor_price),
            "our_price": float(r.our_price),
            "price_diff": float(r.price_diff or 0),
            "price_diff_pct": float(r.price_diff_pct or 0),
            "we_are_cheaper": r.we_are_cheaper,
            "tracked_at": r.tracked_at.isoformat() if r.tracked_at else None,
        }
        for r in rows
    ]


@router.get("/pricing-alerts", dependencies=[Depends(get_current_admin)])
async def get_pricing_alerts(
    is_resolved: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PricingAlert)
        .where(PricingAlert.is_resolved == is_resolved)
        .order_by(PricingAlert.created_at.desc())
        .limit(100)
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "product_id": str(r.product_id),
            "alert_type": r.alert_type,
            "message": r.message,
            "current_value": float(r.current_value or 0),
            "threshold_value": float(r.threshold_value or 0),
            "is_resolved": r.is_resolved,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/pricing-alerts/{alert_id}/resolve", dependencies=[Depends(get_current_admin)])
async def resolve_alert(alert_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PricingAlert).where(PricingAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"resolved": True}


@router.get("/keywords", dependencies=[Depends(get_current_admin)])
async def get_keyword_rankings(
    keyword: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = select(KeywordRanking).order_by(KeywordRanking.tracked_at.desc()).limit(limit)
    if keyword:
        query = query.where(KeywordRanking.keyword.ilike(f"%{keyword}%"))
    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "keyword": r.keyword,
            "target_url": r.target_url,
            "rank": r.rank,
            "previous_rank": r.previous_rank,
            "rank_change": r.rank_change,
            "search_volume": r.search_volume,
            "search_engine": r.search_engine,
            "tracked_at": r.tracked_at.isoformat() if r.tracked_at else None,
        }
        for r in rows
    ]


@router.post("/keywords", dependencies=[Depends(get_current_admin)])
async def add_keyword_ranking(payload: KeywordCreate, db: AsyncSession = Depends(get_db)):
    # Check for previous rank
    prev = await db.execute(
        select(KeywordRanking)
        .where(
            KeywordRanking.keyword == payload.keyword,
            KeywordRanking.search_engine == "google",
        )
        .order_by(KeywordRanking.tracked_at.desc())
        .limit(1)
    )
    prev_row = prev.scalar_one_or_none()
    previous_rank = prev_row.rank if prev_row else None
    rank_change = (previous_rank - payload.rank) if previous_rank else None

    entry = KeywordRanking(
        keyword=payload.keyword,
        target_url=payload.target_url,
        product_id=payload.product_id,
        brand_id=payload.brand_id,
        rank=payload.rank,
        previous_rank=previous_rank,
        rank_change=rank_change,
        search_volume=payload.search_volume,
        difficulty_score=Decimal(str(payload.difficulty_score)) if payload.difficulty_score else None,
    )
    db.add(entry)
    await db.commit()
    return {
        "keyword": entry.keyword,
        "rank": entry.rank,
        "previous_rank": entry.previous_rank,
        "rank_change": entry.rank_change,
        "search_volume": entry.search_volume,
    }


@router.get("/dashboard/profit", dependencies=[Depends(get_current_admin)])
async def profit_dashboard(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    d7 = now - timedelta(days=7)
    d30 = now - timedelta(days=30)

    def _q(since):
        return (
            select(
                func.sum(OrderProfitability.net_profit).label("profit"),
                func.sum(OrderProfitability.revenue).label("revenue"),
                func.count(OrderProfitability.id).label("orders"),
            )
            .join(Order, Order.id == OrderProfitability.order_id)
            .where(Order.created_at >= since)
        )

    r7 = (await db.execute(_q(d7))).one()
    r30 = (await db.execute(_q(d30))).one()

    avg_margin = float((r30.profit or 0) / (r30.revenue or 1) * 100)

    return {
        "profit_7d": float(r7.profit or 0),
        "profit_30d": float(r30.profit or 0),
        "revenue_7d": float(r7.revenue or 0),
        "revenue_30d": float(r30.revenue or 0),
        "orders_7d": r7.orders or 0,
        "orders_30d": r30.orders or 0,
        "avg_margin_30d": round(avg_margin, 2),
    }
