"""Financial / revenue tracking endpoints."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body

from core.redis_client import RedisCache

router = APIRouter()


@router.get("/summary")
async def revenue_summary():
    cache = RedisCache("system")
    report = await cache.get("finance:latest_report") or {}
    return report or {
        "total_revenue_usd": 0,
        "total_costs_usd": 0,
        "net_profit_usd": 0,
        "roi_pct": 0,
        "message": "No financial data yet — run a cycle first",
    }


@router.get("/entries")
async def revenue_entries(limit: int = 50):
    cache = RedisCache("system")
    entries = await cache.get("finance:entries") or []
    return {"entries": entries[-limit:], "count": len(entries)}


@router.post("/record")
async def record_entry(
    amount: float = Body(...),
    entry_type: str = Body(..., pattern="^(revenue|cost)$"),
    source: str = Body("manual"),
    description: str = Body(""),
):
    from datetime import datetime
    cache = RedisCache("system")
    entries = await cache.get("finance:entries") or []
    entry = {
        "amount": amount,
        "type": entry_type,
        "source": source,
        "description": description,
        "recorded_at": datetime.utcnow().isoformat(),
    }
    entries.append(entry)
    await cache.set("finance:entries", entries[-500:], ttl=86400 * 30)
    if entry_type == "revenue":
        current = float(await cache.get("kpi:total_revenue_usd") or 0)
        await cache.set("kpi:total_revenue_usd", current + amount)
    else:
        current = float(await cache.get("kpi:total_costs_usd") or 0)
        await cache.set("kpi:total_costs_usd", current + amount)
    return {"status": "recorded", "entry": entry}


@router.get("/kpis")
async def get_kpis():
    cache = RedisCache("system")
    return {
        "total_revenue_usd": float(await cache.get("kpi:total_revenue_usd") or 0),
        "total_costs_usd": float(await cache.get("kpi:total_costs_usd") or 0),
        "opportunities_discovered": int(await cache.get("kpi:opportunities_discovered") or 0),
        "ceo_kpis": await cache.get("ceo:kpis") or {},
    }


@router.get("/optimisations")
async def get_optimisations():
    cache = RedisCache("system")
    return await cache.get("finance:optimisations") or {"message": "No optimisations yet"}
