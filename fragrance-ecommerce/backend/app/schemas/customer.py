from __future__ import annotations
import re
import uuid
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


def _validate_password_strength(v: str) -> str:
    """Require ≥8 chars, at least one digit, one uppercase, one lowercase."""
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", v):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", v):
        raise ValueError("Password must contain at least one digit")
    return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: uuid.UUID
    email: str
    is_admin: bool


class CustomerAddressCreate(BaseModel):
    address_type: str = "shipping"
    is_default: bool = False
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    company: Optional[str] = None
    address1: str = Field(max_length=255)
    address2: Optional[str] = None
    city: str = Field(max_length=100)
    state: Optional[str] = None
    postal_code: str = Field(max_length=20)
    country: str = Field(default="US", max_length=2)
    phone: Optional[str] = None


class CustomerAddressResponse(CustomerAddressCreate):
    id: uuid.UUID
    customer_id: uuid.UUID
    model_config = {"from_attributes": True}


class CustomerCreate(BaseModel):
    email: EmailStr
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    auth_provider: str = "email"
    marketing_consent: bool = False


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    marketing_consent: Optional[bool] = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: str
    is_active: bool
    is_verified: bool
    is_admin: bool
    marketing_consent: bool
    order_count: int
    total_spent: Decimal
    addresses: List[CustomerAddressResponse] = []
    model_config = {"from_attributes": True}


class CartItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int
    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: uuid.UUID
    session_token: str
    customer_id: Optional[uuid.UUID] = None
    coupon_code: Optional[str] = None
    items: List[CartItemResponse] = []
    model_config = {"from_attributes": True}


class AddToCartRequest(BaseModel):
    product_id: uuid.UUID
    variant_id: Optional[uuid.UUID] = None
    quantity: int = Field(default=1, ge=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=0)


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, v: str) -> str:
        return _validate_password_strength(v)


class WishlistResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    product_id: uuid.UUID
    model_config = {"from_attributes": True}
