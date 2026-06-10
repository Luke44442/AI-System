from __future__ import annotations
import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Brand(BaseModel):
    __tablename__ = "brands"
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(String(2048))
    website_url: Mapped[Optional[str]] = mapped_column(String(2048))
    is_luxury: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    products: Mapped[List["Product"]] = relationship("Product", back_populates="brand")
    def __repr__(self) -> str: return f"<Brand {self.name!r}>"


class Category(BaseModel):
    __tablename__ = "categories"
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    seo_title: Mapped[Optional[str]] = mapped_column(String(70))
    seo_description: Mapped[Optional[str]] = mapped_column(String(160))
    image_url: Mapped[Optional[str]] = mapped_column(String(2048))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attribute_schema_type: Mapped[Optional[str]] = mapped_column(String(50))  # fragrance|sneakers|clothing|bags|accessories|watches|jewelry
    icon: Mapped[Optional[str]] = mapped_column(String(80))
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent: Mapped[Optional["Category"]] = relationship("Category", back_populates="children", remote_side="Category.id")
    children: Mapped[List["Category"]] = relationship("Category", back_populates="parent", lazy="selectin")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")
    attributes: Mapped[List["CategoryAttribute"]] = relationship("CategoryAttribute", back_populates="category", cascade="all, delete-orphan", order_by="CategoryAttribute.sort_order")
    def __repr__(self) -> str: return f"<Category {self.name!r}>"


class CategoryAttribute(BaseModel):
    """Defines an attribute that products in a given category can carry.

    Values are stored on Product.attributes (JSONB), keyed by `key`. This table
    is the schema layer that makes the catalog multi-category: it drives admin
    forms, faceted search/filtering, and category-aware AI enrichment.
    """
    __tablename__ = "category_attributes"
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    data_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)  # string|number|enum|multi_enum|boolean
    options: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    is_filterable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_searchable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_variant_axis: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    category: Mapped["Category"] = relationship("Category", back_populates="attributes")
    def __repr__(self) -> str: return f"<CategoryAttribute {self.key!r} cat={self.category_id}>"


class Supplier(BaseModel):
    __tablename__ = "suppliers"
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")
    base_url: Mapped[Optional[str]] = mapped_column(String(2048))
    credentials: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    default_shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    avg_processing_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    avg_shipping_days: Mapped[int] = mapped_column(Integer, default=14, nullable=False)
    reliability_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=4.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    products: Mapped[List["Product"]] = relationship("Product", back_populates="supplier")
    def __repr__(self) -> str: return f"<Supplier {self.name!r}>"


class Product(BaseModel):
    __tablename__ = "products"
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    brand_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="SET NULL"), index=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    # Multi-category fields (added in migration 003/004)
    product_type: Mapped[str] = mapped_column(String(50), default="fragrance", nullable=False, index=True)
    style_category: Mapped[Optional[str]] = mapped_column(String(100))
    size_options: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    color_options: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    material: Mapped[Optional[str]] = mapped_column(String(255))
    care_instructions: Mapped[Optional[str]] = mapped_column(Text)
    # Fragrance-specific fields (nullable for non-fragrance categories)
    fragrance_family: Mapped[Optional[str]] = mapped_column(String(100))
    concentration: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    gender: Mapped[str] = mapped_column(String(20), default="unisex", nullable=False, index=True)
    volume_ml: Mapped[Optional[int]] = mapped_column(Integer)
    launch_year: Mapped[Optional[int]] = mapped_column(Integer)
    top_notes: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    middle_notes: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    base_notes: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    nose: Mapped[Optional[str]] = mapped_column(String(255))
    supplier_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    shipping_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    website_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    marketplace_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    compare_at_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    inventory_status: Mapped[str] = mapped_column(String(20), default="in_stock", nullable=False, index=True)
    inventory_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_stock_threshold: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(255))
    supplier_url: Mapped[Optional[str]] = mapped_column(String(2048))
    supplier_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    supplier_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    seo_title: Mapped[Optional[str]] = mapped_column(String(70))
    seo_description: Mapped[Optional[str]] = mapped_column(String(160))
    seo_keywords: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    images: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_bestseller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_new_arrival: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    etsy_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    etsy_status: Mapped[str] = mapped_column(String(30), default="not_listed", nullable=False)
    ebay_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    ebay_status: Mapped[str] = mapped_column(String(30), default="not_listed", nullable=False)
    facebook_listing_id: Mapped[Optional[str]] = mapped_column(String(100))
    facebook_status: Mapped[str] = mapped_column(String(30), default="not_listed", nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    ai_generated_listing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revenue_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    rating_avg: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2))
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    brand: Mapped[Optional["Brand"]] = relationship("Brand", back_populates="products")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="products")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="products")
    variants: Mapped[List["ProductVariant"]] = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan", lazy="selectin")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="product", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    marketplace_listings: Mapped[List["MarketplaceListing"]] = relationship("MarketplaceListing", back_populates="product", cascade="all, delete-orphan")  # type: ignore[name-defined]  # noqa: F821
    def __repr__(self) -> str: return f"<Product sku={self.sku!r} name={self.name!r}>"


class ProductVariant(BaseModel):
    __tablename__ = "product_variants"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    volume_ml: Mapped[Optional[int]] = mapped_column(Integer)
    supplier_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    website_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    marketplace_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    inventory_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    supplier_sku: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    product: Mapped["Product"] = relationship("Product", back_populates="variants")
    def __repr__(self) -> str: return f"<ProductVariant sku={self.sku!r}>"
