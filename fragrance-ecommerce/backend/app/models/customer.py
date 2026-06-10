from __future__ import annotations
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    auth_provider: Mapped[str] = mapped_column(String(30), default="email", nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verify_token: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    marketing_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    avg_order_value: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    addresses: Mapped[List["CustomerAddress"]] = relationship("CustomerAddress", back_populates="customer", cascade="all, delete-orphan", lazy="selectin")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer")  # type: ignore[name-defined]  # noqa: F821
    cart: Mapped[Optional["Cart"]] = relationship("Cart", back_populates="customer", uselist=False, cascade="all, delete-orphan")
    wishlists: Mapped[List["Wishlist"]] = relationship("Wishlist", back_populates="customer", cascade="all, delete-orphan")
    @property
    def full_name(self) -> str:
        return " ".join(filter(None, [self.first_name, self.last_name])) or self.email
    def __repr__(self) -> str: return f"<Customer {self.email!r}>"


class CustomerAddress(BaseModel):
    __tablename__ = "customer_addresses"
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    address_type: Mapped[str] = mapped_column(String(20), default="shipping", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(255))
    address1: Mapped[str] = mapped_column(String(255), nullable=False)
    address2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[Optional[str]] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(2), default="US", nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    customer: Mapped["Customer"] = relationship("Customer", back_populates="addresses")


class Cart(BaseModel):
    __tablename__ = "carts"
    customer_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), unique=True, index=True)
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(100))
    customer: Mapped[Optional["Customer"]] = relationship("Customer", back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan", lazy="selectin")


class CartItem(BaseModel):
    __tablename__ = "cart_items"
    __table_args__ = (UniqueConstraint("cart_id", "product_id", "variant_id", name="uq_cart_product_variant"),)
    cart_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"))
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cart: Mapped["Cart"] = relationship("Cart", back_populates="items")


class Wishlist(BaseModel):
    __tablename__ = "wishlists"
    __table_args__ = (UniqueConstraint("customer_id", "product_id", name="uq_customer_product_wishlist"),)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    customer: Mapped["Customer"] = relationship("Customer", back_populates="wishlists")
    product: Mapped[Optional["Product"]] = relationship("Product", lazy="selectin")  # type: ignore[name-defined]  # noqa: F821
