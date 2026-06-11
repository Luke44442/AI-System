from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Collection(BaseModel):
    __tablename__ = "collections"
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(2048))
    banner_url: Mapped[Optional[str]] = mapped_column(String(2048))
    seo_title: Mapped[Optional[str]] = mapped_column(String(70))
    seo_description: Mapped[Optional[str]] = mapped_column(String(160))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    collection_products: Mapped[List["CollectionProduct"]] = relationship("CollectionProduct", back_populates="collection", cascade="all, delete-orphan", lazy="selectin")
    def __repr__(self) -> str: return f"<Collection {self.name!r}>"


class CollectionProduct(BaseModel):
    __tablename__ = "collection_products"
    __table_args__ = (UniqueConstraint("collection_id", "product_id", name="uq_collection_product"),)
    collection_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    collection: Mapped["Collection"] = relationship("Collection", back_populates="collection_products")


class MarketplaceListing(BaseModel):
    __tablename__ = "marketplace_listings"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    listing_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    listing_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    compare_at_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    platform_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    sync_errors: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    # Real timestamps (the DB columns are TIMESTAMPTZ) — the retry sweep
    # compares these against now() so they must not be strings.
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    sync_error: Mapped[Optional[str]] = mapped_column(Text)
    sync_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="marketplace_listings")  # type: ignore[name-defined]  # noqa: F821
    def __repr__(self) -> str: return f"<MarketplaceListing platform={self.platform!r} status={self.status!r}>"


class PricingRule(BaseModel):
    __tablename__ = "pricing_rules"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="all", nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=1.0, nullable=False)
    fixed_addition: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    min_margin_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    max_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    min_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    applies_to: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    def __repr__(self) -> str: return f"<PricingRule {self.name!r} type={self.rule_type!r}>"


class ImportSession(BaseModel):
    __tablename__ = "import_sessions"
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False, index=True)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    mapping_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    initiated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"))
    def __repr__(self) -> str: return f"<ImportSession {self.filename!r} status={self.status!r}>"


class Review(BaseModel):
    __tablename__ = "reviews"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"))
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text)
    reviewer_name: Mapped[Optional[str]] = mapped_column(String(255))
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    platform_source: Mapped[Optional[str]] = mapped_column(String(50))
    platform_review_id: Mapped[Optional[str]] = mapped_column(String(255))
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")  # type: ignore[name-defined]  # noqa: F821
    def __repr__(self) -> str: return f"<Review product_id={self.product_id} rating={self.rating}>"


class DiscountCode(BaseModel):
    __tablename__ = "discount_codes"
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    starts_at: Mapped[Optional[str]] = mapped_column(String(50))
    expires_at: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    applies_to: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    def __repr__(self) -> str: return f"<DiscountCode {self.code!r} type={self.discount_type!r}>"


class AnalyticsEvent(BaseModel):
    __tablename__ = "analytics_events"
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), index=True)
    order_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"))
    properties: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(Text)
    referrer: Mapped[Optional[str]] = mapped_column(Text)
    utm_source: Mapped[Optional[str]] = mapped_column(String(255))
    utm_medium: Mapped[Optional[str]] = mapped_column(String(255))
    utm_campaign: Mapped[Optional[str]] = mapped_column(String(255))
    def __repr__(self) -> str: return f"<AnalyticsEvent {self.event_type!r}>"


class MarketingContent(BaseModel):
    __tablename__ = "marketing_content"
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(500))
    body: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    media_urls: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False, index=True)
    scheduled_at: Mapped[Optional[str]] = mapped_column(String(50))
    published_at: Mapped[Optional[str]] = mapped_column(String(50))
    performance_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    def __repr__(self) -> str: return f"<MarketingContent type={self.content_type!r} platform={self.platform!r}>"


class SystemConfig(BaseModel):
    __tablename__ = "system_config"
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text)
    value_json: Mapped[Optional[dict]] = mapped_column(JSON)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    def __repr__(self) -> str: return f"<SystemConfig {self.key!r}>"


class Notification(BaseModel):
    __tablename__ = "notifications"
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text)
    data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[str]] = mapped_column(String(50))
    def __repr__(self) -> str: return f"<Notification type={self.notification_type!r} read={self.is_read}>"
