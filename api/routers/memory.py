"""Memory system endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Body, Query

from core.redis_client import RedisCache

router = APIRouter()


@router.get("/lessons")
async def get_lessons(limit: int = Query(20, le=100)):
    cache = RedisCache("system")
    lessons = await cache.get("learning:lessons") or []
    return {"lessons": lessons[-limit:], "count": len(lessons)}


@router.get("/knowledge/insights")
async def get_insights():
    cache = RedisCache("system")
    return await cache.get("knowledge:latest_insights") or {"insights": []}


@router.get("/short-term")
async def short_term_snapshot():
    cache = RedisCache("system")
    return {
        "pending_opportunities": len(await cache.get("research:pending_opportunities") or []),
        "qualified_opportunities": len(await cache.get("research:qualified_opportunities") or []),
        "approved_pipeline": len(await cache.get("strategy:approved_pipeline") or []),
        "social_trends": len(await cache.get("research:social_trends") or []),
        "lessons_count": len(await cache.get("learning:lessons") or []),
    }


@router.post("/query")
async def query_memory(query: str = Body(..., embed=True), n_results: int = Body(5)):
    try:
        from core.vector_store import VectorMemory
        vm = VectorMemory("knowledge_base")
        results = await vm.query(query, n_results=n_results)
        return {"results": results, "source": "vector"}
    except Exception:
        cache = RedisCache("system")
        fallback = await cache.get("knowledge:fallback") or []
        return {"results": fallback[:n_results], "source": "redis_fallback"}
