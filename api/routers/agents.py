"""Agent management endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.redis_client import RedisCache

router = APIRouter()


class TaskRequest(BaseModel):
    agent_name: str
    task_type: str
    payload: Dict[str, Any] = {}


@router.get("/", response_model=List[Dict])
async def list_agents():
    """Return status of all registered agents."""
    cache = RedisCache("system")
    agent_names = [
        "SupremeAgent",
        "TrendResearchAgent", "BusinessOpportunityAgent", "MarketAnalysisAgent",
        "CompetitorIntelligenceAgent", "SocialMediaTrendAgent",
        "StrategicPlanningAgent", "BusinessModelAgent", "RiskAnalysisAgent", "ValidationAgent",
        "AutomationBuilderAgent", "WebsiteBuilderAgent", "MarketingAgent",
        "SalesAgent", "ContentAgent", "OutreachAgent",
        "RevenueTrackingAgent", "CostAnalysisAgent", "ProfitOptimizationAgent",
        "KnowledgeManagementAgent", "LearningAgent",
        "PromptOptimizationAgent", "WorkflowOptimizationAgent",
    ]
    result = []
    for name in agent_names:
        info = await cache.get(f"registry:{name}")
        result.append(
            info
            or {
                "name": name,
                "status": "not_started",
                "department": _get_dept(name),
            }
        )
    return result


@router.get("/{agent_name}")
async def get_agent(agent_name: str):
    cache = RedisCache("system")
    info = await cache.get(f"registry:{agent_name}")
    if not info:
        raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found in registry")
    return info


@router.get("/{agent_name}/inbox")
async def get_inbox(agent_name: str, limit: int = 20):
    cache = RedisCache("system")
    messages = await cache.lrange(f"inbox:{agent_name}", 0, limit - 1)
    return {"agent": agent_name, "messages": messages, "count": len(messages)}


@router.post("/task")
async def submit_task(request: TaskRequest):
    """Submit a task to a specific agent."""
    cache = RedisCache("system")
    task = {
        "agent": request.agent_name,
        "type": request.task_type,
        **request.payload,
    }
    await cache.lpush(f"task_queue:{request.agent_name}", task)
    return {"status": "queued", "agent": request.agent_name, "task_type": request.task_type}


@router.get("/departments/summary")
async def departments_summary():
    cache = RedisCache("system")
    departments = {
        "executive": ["SupremeAgent"],
        "research": ["TrendResearchAgent", "BusinessOpportunityAgent", "MarketAnalysisAgent",
                     "CompetitorIntelligenceAgent", "SocialMediaTrendAgent"],
        "strategy": ["StrategicPlanningAgent", "BusinessModelAgent", "RiskAnalysisAgent", "ValidationAgent"],
        "execution": ["AutomationBuilderAgent", "WebsiteBuilderAgent", "MarketingAgent",
                      "SalesAgent", "ContentAgent", "OutreachAgent"],
        "finance": ["RevenueTrackingAgent", "CostAnalysisAgent", "ProfitOptimizationAgent"],
        "self_improvement": ["KnowledgeManagementAgent", "LearningAgent",
                             "PromptOptimizationAgent", "WorkflowOptimizationAgent"],
    }
    result = {}
    for dept, agents in departments.items():
        statuses = []
        for a in agents:
            info = await cache.get(f"registry:{a}")
            statuses.append(info.get("status", "not_started") if info else "not_started")
        running = sum(1 for s in statuses if s == "running")
        result[dept] = {
            "agents": agents,
            "total": len(agents),
            "running": running,
            "idle": sum(1 for s in statuses if s == "idle"),
            "error": sum(1 for s in statuses if s == "error"),
        }
    return result


def _get_dept(name: str) -> str:
    mapping = {
        "SupremeAgent": "executive",
        "TrendResearchAgent": "research", "BusinessOpportunityAgent": "research",
        "MarketAnalysisAgent": "research", "CompetitorIntelligenceAgent": "research",
        "SocialMediaTrendAgent": "research",
        "StrategicPlanningAgent": "strategy", "BusinessModelAgent": "strategy",
        "RiskAnalysisAgent": "strategy", "ValidationAgent": "strategy",
        "AutomationBuilderAgent": "execution", "WebsiteBuilderAgent": "execution",
        "MarketingAgent": "execution", "SalesAgent": "execution",
        "ContentAgent": "execution", "OutreachAgent": "execution",
        "RevenueTrackingAgent": "finance", "CostAnalysisAgent": "finance",
        "ProfitOptimizationAgent": "finance",
        "KnowledgeManagementAgent": "self_improvement", "LearningAgent": "self_improvement",
        "PromptOptimizationAgent": "self_improvement", "WorkflowOptimizationAgent": "self_improvement",
    }
    return mapping.get(name, "unknown")
