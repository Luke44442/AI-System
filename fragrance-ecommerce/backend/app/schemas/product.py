from __future__ import annotations
import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class BrandBase(BaseModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    is_luxury: bool = True
    is_active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    slug: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    is_luxury: Optional[bool] = None
    is_active: Optional[bool] = None


class BrandResponse(BrandBase):
    id: uuid.UUID
    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    icon: Optional[str] = None
    attribute_schema_type: Optional[str] = None
    is_featured: bool = False
    sort_order: int
    product_count: int
    is_active: bool
    parent_id: Optional[uuid.UUID] = None
    children: List["CategoryResponse"] = []
    model_config = {"from_attributes": True}


CategoryResponse.model_rebuild()


class CategoryCreate(BaseModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: Optional[str] = None
    parent_id: Optional[uuid.UUID] = None
    image_url: Optional[str] = None
    sort_order: int = 0
    seo_title: Optional[str] = Field(default=None, max_length=70)
    seo_description: Optional[str] = Field(default=None, max_length=160)
    is_active: bool = True


class SupplierResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    type: str
    base_url: Optional[str] = None
    default_shipping_cost: Decimal
    avg_processing_days: int
    avg_shipping_days: int
    reliability_score: Decimal
    is_active: bool
    model_config = {"from_attributes": True}


class ProductVariantResponse(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    volume_ml: Optional[int] = None
    supplier_cost: Optional[Decimal] = None
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    inventory_quantity: int
    supplier_sku: Optional[str] = None
    is_active: bool
    sort_order: int
    model_config = {"from_attributes": True}


class ProductVariantCreate(BaseModel):
    sku: str = Field(max_length=100)
    name: str = Field(max_length=255)
    volume_ml: Optional[int] = None
    supplier_cost: Optional[Decimal] = None
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    inventory_quantity: int = 0
    supplier_sku: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class ProductCreate(BaseModel):
    sku: str = Field(max_length=100)
    name: str = Field(max_length=500)
    slug: str = Field(max_length=500)
    brand_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    supplier_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    fragrance_family: Optional[str] = Field(default=None, max_length=100)
    concentration: Optional[str] = Field(default=None, max_length=50)
    gender: str = Field(default="unisex", max_length=20)
    volume_ml: Optional[int] = None
    launch_year: Optional[int] = None
    top_notes: Optional[List[str]] = None
    middle_notes: Optional[List[str]] = None
    base_notes: Optional[List[str]] = None
    nose: Optional[str] = None
    supplier_cost: Optional[Decimal] = None
    shipping_cost: Decimal = Decimal("0")
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    inventory_status: str = "in_stock"
    inventory_quantity: int = 0
    supplier_sku: Optional[str] = None
    supplier_url: Optional[str] = None
    seo_title: Optional[str] = Field(default=None, max_length=70)
    seo_description: Optional[str] = Field(default=None, max_length=160)
    seo_keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: bool = True
    is_featured: bool = False
    variants: List[ProductVariantCreate] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    short_description: Optional[str] = None
    fragrance_family: Optional[str] = None
    concentration: Optional[str] = None
    gender: Optional[str] = None
    volume_ml: Optional[int] = None
    top_notes: Optional[List[str]] = None
    middle_notes: Optional[List[str]] = None
    base_notes: Optional[List[str]] = None
    supplier_cost: Optional[Decimal] = None
    shipping_cost: Optional[Decimal] = None
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    inventory_status: Optional[str] = None
    inventory_quantity: Optional[int] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    images: Optional[List[dict]] = None
    attributes: Optional[dict] = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    slug: str
    brand_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    supplier_id: Optional[uuid.UUID] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    product_type: str = "fragrance"
    style_category: Optional[str] = None
    size_options: Optional[List[str]] = None
    color_options: Optional[List[str]] = None
    material: Optional[str] = None
    care_instructions: Optional[str] = None
    attributes: Optional[dict] = None
    fragrance_family: Optional[str] = None
    concentration: Optional[str] = None
    gender: str
    volume_ml: Optional[int] = None
    launch_year: Optional[int] = None
    top_notes: Optional[List[str]] = None
    middle_notes: Optional[List[str]] = None
    base_notes: Optional[List[str]] = None
    nose: Optional[str] = None
    supplier_cost: Optional[Decimal] = None
    shipping_cost: Decimal
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    inventory_status: str
    inventory_quantity: int
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[List[str]] = None
    images: Optional[List[dict]] = None
    tags: Optional[List[str]] = None
    is_active: bool
    is_featured: bool
    is_bestseller: bool
    is_new_arrival: bool
    etsy_status: str
    ebay_status: str
    facebook_status: str
    view_count: int
    order_count: int
    rating_avg: Optional[Decimal] = None
    review_count: int
    brand: Optional[BrandResponse] = None
    variants: List[ProductVariantResponse] = []
    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    id: uuid.UUID
    sku: str
    name: str
    slug: str
    product_type: str = "fragrance"
    style_category: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    attributes: Optional[dict] = None
    fragrance_family: Optional[str] = None
    concentration: Optional[str] = None
    gender: str
    volume_ml: Optional[int] = None
    website_price: Optional[Decimal] = None
    marketplace_price: Optional[Decimal] = None
    inventory_status: str
    inventory_quantity: int
    is_active: bool
    is_featured: bool
    rating_avg: Optional[Decimal] = None
    review_count: int
    images: Optional[List[dict]] = None
    brand: Optional[BrandResponse] = None
    model_config = {"from_attributes": True}


class ProductFilter(BaseModel):
    search: Optional[str] = None
    brand_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    supplier_id: Optional[uuid.UUID] = None
    gender: Optional[str] = None
    concentration: Optional[str] = None
    fragrance_family: Optional[str] = None
    inventory_status: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    etsy_status: Optional[str] = None
    ebay_status: Optional[str] = None


class CollectionCreate(BaseModel):
    name: str = Field(max_length=255)
    slug: str = Field(max_length=255)
    description: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    seo_title: Optional[str] = Field(default=None, max_length=70)
    seo_description: Optional[str] = Field(default=None, max_length=160)
    sort_order: int = 0
    is_active: bool = True
    is_featured: bool = False


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class CollectionResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    banner_url: Optional[str] = None
    sort_order: int
    is_active: bool
    is_featured: bool
    model_config = {"from_attributes": True}
