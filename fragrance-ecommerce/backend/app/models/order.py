from __future__ import annotations
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Order(BaseModel):
    __tablename__ = "orders"
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    guest_email: Mapped[Optional[str]] = mapped_column(String(320))
    customer_name: Mapped[Optional[str]] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(50), default="website", nullable=False, index=True)
    external_order_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    payment_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    fulfillment_status: Mapped[str] = mapped_column(String(50), default="unfulfilled", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    shipping_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    supplier_cost_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    profit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    shipping_address: Mapped[Optional[dict]] = mapped_column(JSON)
    billing_address: Mapped[Optional[dict]] = mapped_column(JSON)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    payment_provider: Mapped[Optional[str]] = mapped_column(String(50))
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    supplier_order_id: Mapped[Optional[str]] = mapped_column(String(255))
    supplier_order_url: Mapped[Optional[str]] = mapped_column(Text)
    supplier_order_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    shipping_method: Mapped[Optional[str]] = mapped_column(String(100))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(255))
    tracking_url: Mapped[Optional[str]] = mapped_column(Text)
    carrier: Mapped[Optional[str]] = mapped_column(String(100))
    discount_code: Mapped[Optional[str]] = mapped_column(String(100))
    customer_note: Mapped[Optional[str]] = mapped_column(Text)
    internal_note: Mapped[Optional[str]] = mapped_column(Text)
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="orders")  # type: ignore[name-defined]  # noqa: F821
    items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    def __repr__(self) -> str: return f"<Order {self.order_number!r} status={self.status!r}>"


class OrderItem(BaseModel):
    __tablename__ = "order_items"
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="SET NULL"))
    sku: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    supplier_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(255))
    fulfillment_status: Mapped[str] = mapped_column(String(50), default="unfulfilled", nullable=False)
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    def __repr__(self) -> str: return f"<OrderItem {self.name!r} qty={self.quantity}>"
