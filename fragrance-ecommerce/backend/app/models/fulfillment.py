"""Supplier fulfillment + observability models.

These tables close the two biggest production gaps:
  * `supplier_orders` — every paid order MUST produce exactly one row here,
    and that row MUST reach a terminal state: placed/shipped/delivered (auto),
    failed (with reason), or manual_queue (human fallback). Nothing is allowed
    to stop silently at "processing" anymore.
  * `system_events` — structured, queryable event log for the order lifecycle,
    supplier API calls, and marketplace sync attempts. The failures dashboard
    reads from here.
  * `marketplace_dead_letters` — listings that exhausted their retry budget.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


# Terminal supplier order states — every order must end in one of these.
SUPPLIER_ORDER_TERMINAL = {"placed", "shipped", "delivered", "failed", "manual_queue", "cancelled"}


class SupplierOrder(BaseModel):
    __tablename__ = "supplier_orders"

    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    # pending → placing → placed → shipped → delivered
    #                   ↘ failed (with reason) / manual_queue (human fallback)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False, index=True)
    external_order_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    external_status: Mapped[Optional[str]] = mapped_column(String(100))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(255))
    carrier: Mapped[Optional[str]] = mapped_column(String(100))
    tracking_url: Mapped[Optional[str]] = mapped_column(Text)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    queued_reason: Mapped[Optional[str]] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    request_payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    response_payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(320))  # admin email or "auto"

    order: Mapped["Order"] = relationship("Order")  # type: ignore[name-defined]  # noqa: F821
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier")  # type: ignore[name-defined]  # noqa: F821

    @property
    def is_terminal(self) -> bool:
        return self.status in SUPPLIER_ORDER_TERMINAL

    def __repr__(self) -> str:
        return f"<SupplierOrder order={self.order_id} status={self.status!r}>"


class SystemEvent(BaseModel):
    __tablename__ = "system_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), default="info", nullable=False, index=True)  # info|warning|error|critical
    message: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), index=True)
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), index=True)

    def __repr__(self) -> str:
        return f"<SystemEvent {self.event_type!r} severity={self.severity!r}>"


class MarketplaceDeadLetter(BaseModel):
    __tablename__ = "marketplace_dead_letters"

    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("marketplace_listings.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), nullable=False)  # create|update|inventory|price|delete
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<MarketplaceDeadLetter platform={self.platform!r} op={self.operation!r}>"
