"""System control endpoints — start/stop cycles, view logs."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from core.config import settings
from core.redis_client import RedisCache

router = APIRouter()
logger = logging.getLogger(__name__)

_running_task: asyncio.Task | None = None


@router.post("/cycle/start")
async def start_cycle(background_tasks: BackgroundTasks):
    """Start a single research-to-improvement cycle in the background."""
    background_tasks.add_task(_run_cycle)
    return {"status": "started", "message": "Cycle started in background"}


@router.get("/cycle/status")
async def cycle_status():
    cache = RedisCache("system")
    logs = await cache.lrange("activity:recent_log", 0, 4)
    return {"recent_cycles": logs, "count": len(logs)}


@router.get("/dashboard")
async def dashboard_data():
    """Aggregate data for the real-time dashboard."""
    cache = RedisCache("system")
    return {
        "ceo": await cache.get("ceo:kpis") or {},
        "ceo_review": await cache.get("ceo:latest_review") or {},
        "finance": await cache.get("finance:latest_report") or {},
        "approved_opportunities": len(await cache.get("strategy:approved_pipeline") or []),
        "pending_research": len(await cache.get("research:pending_opportunities") or []),
        "knowledge_insights": await cache.get("knowledge:latest_insights") or {},
        "workflow_optimisations": await cache.get("workflow:optimisations") or {},
        "system_config": {
            "opportunity_threshold": settings.opportunity_score_threshold,
            "max_budget_usd": settings.max_execution_budget_usd,
            "llm_provider": settings.primary_llm_provider,
            "env": settings.app_env,
        },
    }


@router.get("/logs")
async def get_logs(limit: int = 20):
    cache = RedisCache("system")
    logs = await cache.lrange("activity:recent_log", 0, limit - 1)
    return {"logs": logs}


@router.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "llm_provider": settings.primary_llm_provider,
        "llm_model": settings.active_llm_model,
        "opportunity_threshold": settings.opportunity_score_threshold,
        "max_execution_budget": settings.max_execution_budget_usd,
        "research_interval_minutes": settings.research_loop_interval_minutes,
    }


@router.delete("/cache/flush")
async def flush_cache(confirm: str = "no"):
    if confirm != "yes":
        raise HTTPException(status_code=400, detail="Pass ?confirm=yes to flush cache")
    import redis.asyncio as aioredis
    r = aioredis.from_url(settings.redis_url)
    await r.flushdb()
    await r.aclose()
    return {"status": "flushed"}


async def _run_cycle():
    try:
        from workflows.main_loop import run_one_cycle
        await run_one_cycle()
    except Exception as exc:
        logger.error("Cycle error: %s", exc, exc_info=True)
