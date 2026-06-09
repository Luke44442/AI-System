from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.core.auth import get_current_admin
from app.models.content import EmailSubscriber
import structlog

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/email", tags=["email"])


class SubscribeRequest(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    source: Optional[str] = "website"


class UnsubscribeRequest(BaseModel):
    email: EmailStr


@router.post("/subscribe")
async def subscribe(payload: SubscribeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailSubscriber).where(EmailSubscriber.email == payload.email.lower())
    )
    subscriber = result.scalar_one_or_none()

    if subscriber:
        if subscriber.status == "unsubscribed":
            subscriber.status = "subscribed"
            subscriber.unsubscribed_at = None
            subscriber.subscribed_at = datetime.now(timezone.utc)
        if payload.first_name and not subscriber.first_name:
            subscriber.first_name = payload.first_name
    else:
        subscriber = EmailSubscriber(
            email=payload.email.lower(),
            first_name=payload.first_name,
            last_name=payload.last_name,
            status="subscribed",
            source=payload.source or "website",
            subscribed_at=datetime.now(timezone.utc),
        )
        db.add(subscriber)

    await db.commit()
    return {"subscribed": True, "email": payload.email.lower()}


@router.post("/unsubscribe")
async def unsubscribe(payload: UnsubscribeRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailSubscriber).where(EmailSubscriber.email == payload.email.lower())
    )
    subscriber = result.scalar_one_or_none()
    if not subscriber:
        raise HTTPException(status_code=404, detail="Email not found")

    subscriber.status = "unsubscribed"
    subscriber.unsubscribed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"unsubscribed": True}


@router.get("/subscribers", dependencies=[Depends(get_current_admin)])
async def list_subscribers(
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(EmailSubscriber).order_by(EmailSubscriber.subscribed_at.desc())
    if status:
        query = query.where(EmailSubscriber.status == status)
    if source:
        query = query.where(EmailSubscriber.source == source)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar_one()

    result = await db.execute(query.offset(offset).limit(limit))
    rows = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(r.id),
                "email": r.email,
                "first_name": r.first_name,
                "status": r.status,
                "source": r.source,
                "subscribed_at": r.subscribed_at.isoformat() if r.subscribed_at else None,
                "open_count": r.open_count,
                "click_count": r.click_count,
            }
            for r in rows
        ],
    }


@router.get("/subscribers/count", dependencies=[Depends(get_current_admin)])
async def subscriber_counts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailSubscriber.status, func.count(EmailSubscriber.id).label("cnt"))
        .group_by(EmailSubscriber.status)
    )
    counts = {row.status: row.cnt for row in result.all()}
    return {
        "total": sum(counts.values()),
        "subscribed": counts.get("subscribed", 0),
        "unsubscribed": counts.get("unsubscribed", 0),
        "bounced": counts.get("bounced", 0),
    }
