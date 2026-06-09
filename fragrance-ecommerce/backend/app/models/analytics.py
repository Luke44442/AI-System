from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class SupplierCostHistory(BaseModel):
    __tablename__ = "supplier_cost_history"

    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    change_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    supplier: Mapped["Supplier"] = relationship("Supplier")  # type: ignore[name-defined]
    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<SupplierCostHistory product={self.product_id} {self.old_cost}->{self.new_cost}>"


class OrderProfitability(BaseModel):
    __tablename__ = "order_profitability"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    revenue: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    supplier_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    platform_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    stripe_fee: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    other_fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    gross_profit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    net_profit: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    margin_pct: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="website", index=True)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order: Mapped["Order"] = relationship("Order")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<OrderProfitability order={self.order_id} margin={self.margin_pct}%>"


class KeywordRanking(BaseModel):
    __tablename__ = "keyword_rankings"

    keyword: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), index=True)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), index=True)
    search_engine: Mapped[str] = mapped_column(String(50), nullable=False, default="google", index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_rank: Mapped[Optional[int]] = mapped_column(Integer)
    rank_change: Mapped[Optional[int]] = mapped_column(Integer)
    search_volume: Mapped[Optional[int]] = mapped_column(Integer)
    difficulty_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    product: Mapped[Optional["Product"]] = relationship("Product")  # type: ignore[name-defined]
    brand: Mapped[Optional["Brand"]] = relationship("Brand")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<KeywordRanking {self.keyword!r} rank={self.rank}>"


class CompetitorPrice(BaseModel):
    __tablename__ = "competitor_prices"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    competitor_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    competitor_url: Mapped[Optional[str]] = mapped_column(Text)
    competitor_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    our_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    price_diff_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    we_are_cheaper: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<CompetitorPrice product={self.product_id} {self.competitor_name}={self.competitor_price}>"


class PricingAlert(BaseModel):
    __tablename__ = "pricing_alerts"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    current_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    threshold_value: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<PricingAlert product={self.product_id} type={self.alert_type} resolved={self.is_resolved}>"
