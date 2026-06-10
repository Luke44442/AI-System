from __future__ import annotations
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import settings
from app.database import get_db
from app.models.customer import Customer, CustomerAddress, Cart, CartItem, Wishlist
from app.models.product import Product
from app.schemas.product import ProductListItem
from app.schemas.customer import (
    LoginRequest, RegisterRequest, TokenResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerAddressCreate, CustomerAddressResponse,
    CartResponse, AddToCartRequest, UpdateCartItemRequest, WishlistResponse,
    ForgotPasswordRequest, ResetPasswordRequest,
)
from app.schemas.common import SuccessResponse
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.email import send_password_reset_email, send_welcome_email

router = APIRouter(prefix="/customers", tags=["customers"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_or_create_cart(db: AsyncSession, customer: Customer) -> Cart:
    result = await db.execute(
        select(Cart).where(Cart.customer_id == customer.id).options(selectinload(Cart.items))
    )
    cart = result.scalar_one_or_none()
    if not cart:
        cart = Cart(customer_id=customer.id, session_token=secrets.token_urlsafe(24))
        db.add(cart)
        await db.flush()
    return cart


@auth_router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Customer).where(Customer.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    customer = Customer(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        auth_provider="email",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    try:
        send_welcome_email(customer.email, customer.first_name)
    except Exception:
        pass  # never block registration on email
    token = create_access_token(str(customer.id), {"email": customer.email, "is_admin": customer.is_admin})
    return TokenResponse(access_token=token, customer_id=customer.id, email=customer.email, is_admin=customer.is_admin)


@auth_router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Issue a password reset token. Always returns success to avoid user enumeration."""
    result = await db.execute(select(Customer).where(Customer.email == payload.email.lower().strip()))
    customer = result.scalar_one_or_none()
    if customer and customer.is_active:
        token = secrets.token_urlsafe(32)
        customer.password_reset_token = token
        customer.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        frontend = settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "http://localhost:3000"
        reset_url = f"{frontend}/auth/reset-password?token={token}"
        try:
            send_password_reset_email(customer.email, reset_url)
        except Exception:
            pass
    return SuccessResponse(message="If an account exists for that email, a reset link has been sent.")


@auth_router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.password_reset_token == payload.token))
    customer = result.scalar_one_or_none()
    if not customer or not customer.password_reset_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    expires = customer.password_reset_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")
    customer.password_hash = hash_password(payload.new_password)
    customer.password_reset_token = None
    customer.password_reset_expires = None
    await db.commit()
    return SuccessResponse(message="Password updated. You can now sign in.")


@auth_router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer).where(Customer.email == payload.email))
    customer = result.scalar_one_or_none()
    if not customer or not customer.password_hash or not verify_password(payload.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not customer.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(str(customer.id), {"email": customer.email, "is_admin": customer.is_admin})
    return TokenResponse(access_token=token, customer_id=customer.id, email=customer.email, is_admin=customer.is_admin)


@router.get("/me", response_model=CustomerResponse)
async def get_me(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Customer).where(Customer.id == current_user.id).options(selectinload(Customer.addresses))
    )
    return result.scalar_one()


@router.patch("/me", response_model=CustomerResponse)
async def update_me(payload: CustomerUpdate, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(current_user, k, v)
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/me/addresses", response_model=list[CustomerAddressResponse])
async def get_addresses(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CustomerAddress).where(CustomerAddress.customer_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/me/addresses", response_model=CustomerAddressResponse, status_code=201)
async def add_address(payload: CustomerAddressCreate, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if payload.is_default:
        await db.execute(
            CustomerAddress.__table__.update()
            .where(CustomerAddress.customer_id == current_user.id)
            .values(is_default=False)
        )
    address = CustomerAddress(customer_id=current_user.id, **payload.model_dump())
    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


@router.delete("/me/addresses/{address_id}")
async def delete_address(address_id: uuid.UUID, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CustomerAddress).where(CustomerAddress.id == address_id, CustomerAddress.customer_id == current_user.id)
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    await db.delete(address)
    await db.commit()
    return SuccessResponse(message="Address deleted")


# ---------------------------------------------------------------------------
# Server-side cart (persists across devices for logged-in customers)
# ---------------------------------------------------------------------------
@router.get("/me/cart", response_model=CartResponse)
async def get_cart(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await _get_or_create_cart(db, current_user)


@router.post("/me/cart/items", response_model=CartResponse, status_code=201)
async def add_to_cart(payload: AddToCartRequest, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await _get_or_create_cart(db, current_user)
    existing = next(
        (i for i in cart.items if i.product_id == payload.product_id and i.variant_id == payload.variant_id),
        None,
    )
    if existing:
        existing.quantity += payload.quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=payload.product_id,
                        variant_id=payload.variant_id, quantity=payload.quantity))
    await db.commit()
    return await _get_or_create_cart(db, current_user)


@router.patch("/me/cart/items/{item_id}", response_model=CartResponse)
async def update_cart_item(item_id: uuid.UUID, payload: UpdateCartItemRequest,
                           current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await _get_or_create_cart(db, current_user)
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    if payload.quantity <= 0:
        await db.delete(item)
    else:
        item.quantity = payload.quantity
    await db.commit()
    return await _get_or_create_cart(db, current_user)


@router.delete("/me/cart/items/{item_id}", response_model=CartResponse)
async def remove_cart_item(item_id: uuid.UUID, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await _get_or_create_cart(db, current_user)
    item = next((i for i in cart.items if i.id == item_id), None)
    if item:
        await db.delete(item)
        await db.commit()
    return await _get_or_create_cart(db, current_user)


@router.delete("/me/cart", response_model=SuccessResponse)
async def clear_cart(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await _get_or_create_cart(db, current_user)
    for item in list(cart.items):
        await db.delete(item)
    await db.commit()
    return SuccessResponse(message="Cart cleared")


@router.get("/me/wishlist")
async def get_wishlist(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Returns {items: [...]} so the frontend wishlist page can map item.product."""
    result = await db.execute(
        select(Wishlist).where(Wishlist.customer_id == current_user.id)
        .options(selectinload(Wishlist.product).selectinload(Product.brand))
    )
    wishlist_items = result.scalars().all()
    return {
        "items": [
            {"id": str(w.id), "product_id": str(w.product_id),
             "product": ProductListItem.model_validate(w.product).model_dump(mode="json") if w.product else None}
            for w in wishlist_items
        ]
    }


@router.post("/me/wishlist/{product_id}", response_model=WishlistResponse, status_code=201)
async def add_to_wishlist(product_id: uuid.UUID, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Wishlist).where(Wishlist.customer_id == current_user.id, Wishlist.product_id == product_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in wishlist")
    item = Wishlist(customer_id=current_user.id, product_id=product_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/me/wishlist/{product_id}")
async def remove_from_wishlist(product_id: uuid.UUID, current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Wishlist).where(Wishlist.customer_id == current_user.id, Wishlist.product_id == product_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Not in wishlist")
    await db.delete(item)
    await db.commit()
    return SuccessResponse(message="Removed from wishlist")
