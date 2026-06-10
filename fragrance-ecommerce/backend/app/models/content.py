from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class ProductEnrichment(BaseModel):
    __tablename__ = "product_enrichment"

    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Fragrance notes
    top_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    middle_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    base_notes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    fragrance_family: Mapped[Optional[str]] = mapped_column(String(100))

    # Season scores (0-10)
    season_spring: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    season_summer: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    season_fall: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    season_winter: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))

    # Occasion scores (0-10)
    occasion_casual: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    occasion_formal: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    occasion_evening: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    occasion_office: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    occasion_outdoor: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    occasion_sport: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))

    # Quality/character scores (0-10)
    longevity_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    projection_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    uniqueness_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    value_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))

    # AI-generated content
    similar_fragrances: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    alternative_recommendations: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ai_description: Mapped[Optional[str]] = mapped_column(Text)
    ai_short_description: Mapped[Optional[str]] = mapped_column(Text)
    tiktok_hook: Mapped[Optional[str]] = mapped_column(Text)
    ai_generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    product: Mapped["Product"] = relationship("Product")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<ProductEnrichment product={self.product_id}>"


class ContentItem(BaseModel):
    __tablename__ = "content_items"

    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    excerpt: Mapped[Optional[str]] = mapped_column(Text)
    body: Mapped[Optional[str]] = mapped_column(Text)

    # SEO fields
    seo_title: Mapped[Optional[str]] = mapped_column(String(70))
    seo_description: Mapped[Optional[str]] = mapped_column(String(160))
    seo_keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    featured_image_url: Mapped[Optional[str]] = mapped_column(Text)

    # Associations
    product_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    brand_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Publishing
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    author: Mapped[str] = mapped_column(String(255), nullable=False, default="Aurevia Team")

    # Schema / internal links
    schema_markup: Mapped[Optional[dict]] = mapped_column(JSON)
    internal_links: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Engagement
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    read_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    def __repr__(self) -> str:
        return f"<ContentItem {self.content_type!r} {self.slug!r}>"


class TikTokContent(BaseModel):
    __tablename__ = "tiktok_content"

    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), index=True)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), index=True)

    content_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    hook: Mapped[Optional[str]] = mapped_column(Text)
    script: Mapped[Optional[str]] = mapped_column(Text)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    hashtags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    trending_audio_suggestions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # Targeting
    target_age_range: Mapped[Optional[str]] = mapped_column(String(50))
    target_gender: Mapped[Optional[str]] = mapped_column(String(20))
    estimated_views: Mapped[Optional[int]] = mapped_column(Integer)

    # Publishing / performance
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft", index=True)
    platform_post_id: Mapped[Optional[str]] = mapped_column(String(255))
    actual_views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    product: Mapped[Optional["Product"]] = relationship("Product")  # type: ignore[name-defined]
    brand: Mapped[Optional["Brand"]] = relationship("Brand")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<TikTokContent {self.content_type!r} status={self.status!r}>"


class EmailSubscriber(BaseModel):
    __tablename__ = "email_subscribers"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255))
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="subscribed", index=True)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_email_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    open_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    customer: Mapped[Optional["Customer"]] = relationship("Customer")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<EmailSubscriber {self.email!r} status={self.status!r}>"
