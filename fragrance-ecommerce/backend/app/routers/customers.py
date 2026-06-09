from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.customer import Customer, CustomerAddress, Cart, CartItem, Wishlist
from app.schemas.customer import (
    LoginRequest, RegisterRequest, TokenResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    CustomerAddressCreate, CustomerAddressResponse,
    CartResponse, AddToCartRequest, WishlistResponse,
)
from app.schemas.common import SuccessResponse
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/customers", tags=["customers"])
auth_router = APIRouter(prefix="/auth", tags=["auth"])


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
    token = create_access_token(str(customer.id), {"email": customer.email, "is_admin": customer.is_admin})
    return TokenResponse(access_token=token, customer_id=customer.id, email=customer.email, is_admin=customer.is_admin)


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


@router.get("/me/wishlist", response_model=list[WishlistResponse])
async def get_wishlist(current_user: Customer = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Wishlist).where(Wishlist.customer_id == current_user.id))
    return result.scalars().all()


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
