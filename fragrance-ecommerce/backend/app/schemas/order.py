from __future__ import annotations
import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class ShippingAddress(BaseModel):
    first_name: str
    last_name: str
    company: Optional[str] = None
    address1: str
    address2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "US"
    phone: Optional[str] = None


class BillingAddress(ShippingAddress):
    pass


class OrderItemCreate(BaseModel):
    product_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    sku: str
    name: str
    quantity: int = Field(ge=1)
    unit_price: Decimal
    supplier_cost: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: Optional[uuid.UUID] = None
    variant_id: Optional[uuid.UUID] = None
    sku: str
    name: str
    image_url: Optional[str] = None
    quantity: int
    unit_price: Decimal
    supplier_cost: Decimal
    discount_amount: Decimal
    total: Decimal
    supplier_sku: Optional[str] = None
    fulfillment_status: str
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_id: Optional[uuid.UUID] = None
    guest_email: Optional[str] = None
    channel: str = "website"
    items: List[OrderItemCreate]
    shipping_address: Optional[ShippingAddress] = None
    billing_address: Optional[BillingAddress] = None
    shipping_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    discount_code: Optional[str] = None
    payment_method: Optional[str] = None
    customer_note: Optional[str] = None
    currency: str = "USD"


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    carrier: Optional[str] = None
    shipping_method: Optional[str] = None
    internal_note: Optional[str] = None
    supplier_order_id: Optional[str] = None
    supplier_order_url: Optional[str] = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: Optional[uuid.UUID] = None
    guest_email: Optional[str] = None
    customer_name: Optional[str] = None
    channel: str
    status: str
    payment_status: str
    fulfillment_status: str
    subtotal: Decimal
    shipping_amount: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total: Decimal
    currency: str
    profit_amount: Decimal
    shipping_address: Optional[dict] = None
    billing_address: Optional[dict] = None
    payment_method: Optional[str] = None
    payment_provider: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    carrier: Optional[str] = None
    discount_code: Optional[str] = None
    customer_note: Optional[str] = None
    items: List[OrderItemResponse] = []
    model_config = {"from_attributes": True}


class OrderListItem(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: Optional[uuid.UUID] = None
    customer_name: Optional[str] = None
    channel: str
    status: str
    payment_status: str
    fulfillment_status: str
    total: Decimal
    currency: str
    item_count: int = 0
    model_config = {"from_attributes": True}


class OrderFilter(BaseModel):
    search: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    channel: Optional[str] = None
    customer_id: Optional[uuid.UUID] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    min_total: Optional[Decimal] = None
    max_total: Optional[Decimal] = None
