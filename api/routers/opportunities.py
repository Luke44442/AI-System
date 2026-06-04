"""Opportunity pipeline endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query

from core.config import settings
from core.redis_client import RedisCache
from scoring.opportunity_scorer import OpportunityScorer

router = APIRouter()
scorer = OpportunityScorer()


@router.get("/pipeline")
async def get_pipeline():
    cache = RedisCache("system")
    approved = await cache.get("strategy:approved_pipeline") or []
    qualified = await cache.get("research:qualified_opportunities") or []
    pending = await cache.get("research:pending_opportunities") or []
    return {
        "pipeline": {
            "approved": {"count": len(approved), "items": approved[:10]},
            "qualified": {"count": len(qualified), "items": qualified[:10]},
            "pending": {"count": len(pending), "items": pending[:10]},
        },
        "total": len(approved) + len(qualified) + len(pending),
    }


@router.get("/approved")
async def get_approved(limit: int = Query(20, le=100)):
    cache = RedisCache("system")
    approved = await cache.get("strategy:approved_pipeline") or []
    return {"opportunities": approved[:limit], "count": len(approved)}


@router.get("/score")
async def score_opportunity(
    title: str = Query(...),
    description: str = Query(""),
    profit_potential: int = Query(50),
    difficulty: int = Query(50),
    startup_cost: int = Query(50),
    time_required: int = Query(50),
    automation_potential: int = Query(50),
    scalability: int = Query(50),
    risk_level: int = Query(50),
):
    opp = {
        "title": title,
        "description": description,
        "profit_potential": profit_potential,
        "difficulty": difficulty,
        "startup_cost": startup_cost,
        "time_required": time_required,
        "automation_potential": automation_potential,
        "scalability": scalability,
        "risk_level": risk_level,
    }
    scorecard = scorer.generate_scorecard(opp)
    return scorecard


@router.post("/score/batch")
async def score_batch(opportunities: List[Dict[str, Any]] = Body(...)):
    return {"scored": scorer.score_batch(opportunities)}


@router.get("/threshold")
async def get_threshold():
    return {
        "threshold": settings.opportunity_score_threshold,
        "description": "Opportunities must score above this to proceed to execution",
    }


@router.get("/leaderboard")
async def leaderboard():
    cache = RedisCache("system")
    approved = await cache.get("strategy:approved_pipeline") or []
    sorted_opps = sorted(approved, key=lambda x: x.get("overall_score", 0), reverse=True)
    return {"leaderboard": sorted_opps[:20]}
