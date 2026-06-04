"""
Main autonomous research → analyse → validate → plan → execute → measure → learn → improve loop.
Implemented as a LangGraph StateGraph.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

logger = logging.getLogger(__name__)


# ─── State ────────────────────────────────────────────────────────────────────

class SystemState(TypedDict):
    cycle_id: str
    phase: str
    raw_opportunities: List[Dict]
    qualified_opportunities: List[Dict]
    scored_opportunities: List[Dict]
    approved_opportunities: List[Dict]
    execution_plans: List[Dict]
    metrics: Dict[str, Any]
    lessons: List[Dict]
    errors: List[str]
    iteration: int
    timestamp: str


def _initial_state() -> SystemState:
    return SystemState(
        cycle_id=datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
        phase="research",
        raw_opportunities=[],
        qualified_opportunities=[],
        scored_opportunities=[],
        approved_opportunities=[],
        execution_plans=[],
        metrics={},
        lessons=[],
        errors=[],
        iteration=0,
        timestamp=datetime.utcnow().isoformat(),
    )


# ─── Node functions ───────────────────────────────────────────────────────────

async def research_node(state: SystemState) -> SystemState:
    """Run all research agents to discover opportunities."""
    logger.info("[Workflow] Phase: RESEARCH (cycle %s)", state["cycle_id"])
    from agents.research.trend_research_agent import TrendResearchAgent
    from agents.research.social_media_trend_agent import SocialMediaTrendAgent
    from core.redis_client import RedisCache

    cache = RedisCache("system")
    try:
        # Trigger research agents
        agent = TrendResearchAgent()
        await agent.run_cycle()
        social = SocialMediaTrendAgent()
        await social.run_cycle()
        # Read results
        discovered = await cache.get("research:pending_opportunities") or []
        return {**state, "phase": "qualify", "raw_opportunities": discovered[:20]}
    except Exception as exc:
        logger.error("[Workflow:research] Error: %s", exc)
        return {**state, "phase": "qualify", "errors": state["errors"] + [str(exc)]}


async def qualify_node(state: SystemState) -> SystemState:
    """Qualify raw opportunities for further analysis."""
    logger.info("[Workflow] Phase: QUALIFY (%d raw)", len(state["raw_opportunities"]))
    from agents.research.business_opportunity_agent import BusinessOpportunityAgent

    try:
        agent = BusinessOpportunityAgent()
        qualified = []
        for opp in state["raw_opportunities"][:10]:
            result = await agent.execute_task({"opportunity": opp})
            q = result.get("qualified_opportunity", {})
            if q.get("qualified"):
                qualified.append(q)
        return {**state, "phase": "score", "qualified_opportunities": qualified}
    except Exception as exc:
        logger.error("[Workflow:qualify] Error: %s", exc)
        return {**state, "phase": "score", "errors": state["errors"] + [str(exc)]}


async def score_node(state: SystemState) -> SystemState:
    """Score qualified opportunities."""
    logger.info("[Workflow] Phase: SCORE (%d qualified)", len(state["qualified_opportunities"]))
    from agents.strategy.strategic_planning_agent import StrategicPlanningAgent

    try:
        agent = StrategicPlanningAgent()
        scored = []
        for opp in state["qualified_opportunities"]:
            result = await agent.execute_task({"opportunity": opp, "skip_plan": True})
            scored.append(result.get("opportunity", opp))
        return {**state, "phase": "validate", "scored_opportunities": scored}
    except Exception as exc:
        logger.error("[Workflow:score] Error: %s", exc)
        return {**state, "phase": "validate", "errors": state["errors"] + [str(exc)]}


async def validate_node(state: SystemState) -> SystemState:
    """Validate top-scoring opportunities."""
    logger.info("[Workflow] Phase: VALIDATE")
    from agents.strategy.validation_agent import ValidationAgent
    from core.config import settings

    try:
        agent = ValidationAgent()
        validated = []
        for opp in state["scored_opportunities"]:
            if opp.get("overall_score", 0) >= settings.opportunity_score_threshold:
                result = await agent.execute_task({"opportunity": opp})
                v = result.get("validation", {})
                if v.get("validated"):
                    opp["validation"] = v
                    validated.append(opp)
        return {**state, "phase": "plan", "approved_opportunities": validated}
    except Exception as exc:
        logger.error("[Workflow:validate] Error: %s", exc)
        return {**state, "phase": "plan", "errors": state["errors"] + [str(exc)]}


async def plan_node(state: SystemState) -> SystemState:
    """Create execution plans for approved opportunities."""
    logger.info("[Workflow] Phase: PLAN (%d approved)", len(state["approved_opportunities"]))
    from agents.strategy.strategic_planning_agent import StrategicPlanningAgent
    from agents.strategy.business_model_agent import BusinessModelAgent

    try:
        planner = StrategicPlanningAgent()
        modeler = BusinessModelAgent()
        plans = []
        for opp in state["approved_opportunities"][:3]:  # Cap at 3 to control costs
            plan_result = await planner._create_execution_plan(opp)
            model_result = await modeler.execute_task({"opportunity": opp})
            plans.append({
                "opportunity": opp,
                "execution_plan": plan_result,
                "business_model": model_result.get("business_model", {}),
            })
        return {**state, "phase": "execute", "execution_plans": plans}
    except Exception as exc:
        logger.error("[Workflow:plan] Error: %s", exc)
        return {**state, "phase": "execute", "errors": state["errors"] + [str(exc)]}


async def execute_node(state: SystemState) -> SystemState:
    """Kick off execution for planned opportunities."""
    logger.info("[Workflow] Phase: EXECUTE (%d plans)", len(state["execution_plans"]))
    from agents.execution.automation_builder_agent import AutomationBuilderAgent
    from agents.execution.marketing_agent import MarketingAgent

    try:
        for plan_bundle in state["execution_plans"]:
            opp = plan_bundle["opportunity"]
            builder = AutomationBuilderAgent()
            await builder.execute_task({"opportunity": opp})
            marketer = MarketingAgent()
            await marketer.execute_task({"opportunity": opp})
        return {**state, "phase": "measure"}
    except Exception as exc:
        logger.error("[Workflow:execute] Error: %s", exc)
        return {**state, "phase": "measure", "errors": state["errors"] + [str(exc)]}


async def measure_node(state: SystemState) -> SystemState:
    """Collect metrics from finance agents."""
    logger.info("[Workflow] Phase: MEASURE")
    from agents.finance.revenue_tracking_agent import RevenueTrackingAgent

    try:
        agent = RevenueTrackingAgent()
        result = await agent.execute_task({"type": "report"})
        return {**state, "phase": "learn", "metrics": result.get("report", {})}
    except Exception as exc:
        logger.error("[Workflow:measure] Error: %s", exc)
        return {**state, "phase": "learn", "errors": state["errors"] + [str(exc)]}


async def learn_node(state: SystemState) -> SystemState:
    """Extract lessons from outcomes."""
    logger.info("[Workflow] Phase: LEARN")
    from agents.self_improvement.learning_agent import LearningAgent

    try:
        agent = LearningAgent()
        result = await agent.execute_task({
            "activity_data": state.get("execution_plans", []),
            "outcomes": state.get("metrics", {}),
        })
        return {**state, "phase": "improve", "lessons": result.get("lessons", {}).get("lessons", [])}
    except Exception as exc:
        logger.error("[Workflow:learn] Error: %s", exc)
        return {**state, "phase": "improve", "errors": state["errors"] + [str(exc)]}


async def improve_node(state: SystemState) -> SystemState:
    """Apply improvements based on lessons."""
    logger.info("[Workflow] Phase: IMPROVE — cycle complete")
    from agents.self_improvement.knowledge_management_agent import KnowledgeManagementAgent
    from core.redis_client import RedisCache

    try:
        km = KnowledgeManagementAgent()
        for lesson in state.get("lessons", []):
            await km.execute_task({
                "type": "store",
                "content": f"{lesson.get('title', '')}: {lesson.get('description', '')}",
                "metadata": lesson,
            })
        # Log cycle completion
        cache = RedisCache("system")
        await cache.lpush(
            "activity:recent_log",
            {
                "cycle_id": state["cycle_id"],
                "iteration": state["iteration"],
                "opportunities_discovered": len(state["raw_opportunities"]),
                "approved": len(state["approved_opportunities"]),
                "lessons": len(state.get("lessons", [])),
                "errors": len(state.get("errors", [])),
                "completed_at": datetime.utcnow().isoformat(),
            },
        )
    except Exception as exc:
        logger.error("[Workflow:improve] Error: %s", exc)
    return {**state, "phase": "research", "iteration": state["iteration"] + 1}


# ─── Routing ──────────────────────────────────────────────────────────────────

def route_after_research(state: SystemState) -> str:
    return "qualify" if state["raw_opportunities"] else "measure"


def route_after_score(state: SystemState) -> str:
    has_above_threshold = any(
        o.get("overall_score", 0) >= 65 for o in state["scored_opportunities"]
    )
    return "validate" if has_above_threshold else "measure"


def route_after_validate(state: SystemState) -> str:
    return "plan" if state["approved_opportunities"] else "measure"


def route_after_plan(state: SystemState) -> str:
    return "execute" if state["execution_plans"] else "measure"


def should_continue(state: SystemState) -> str:
    """After improve, always loop back (perpetual system)."""
    return END  # Return END to stop after one cycle; remove for perpetual loop


# ─── Graph assembly ───────────────────────────────────────────────────────────

def build_main_workflow() -> StateGraph:
    graph = StateGraph(SystemState)

    graph.add_node("research", research_node)
    graph.add_node("qualify", qualify_node)
    graph.add_node("score", score_node)
    graph.add_node("validate", validate_node)
    graph.add_node("plan", plan_node)
    graph.add_node("execute", execute_node)
    graph.add_node("measure", measure_node)
    graph.add_node("learn", learn_node)
    graph.add_node("improve", improve_node)

    graph.add_edge(START, "research")
    graph.add_conditional_edges("research", route_after_research, {"qualify": "qualify", "measure": "measure"})
    graph.add_edge("qualify", "score")
    graph.add_conditional_edges("score", route_after_score, {"validate": "validate", "measure": "measure"})
    graph.add_conditional_edges("validate", route_after_validate, {"plan": "plan", "measure": "measure"})
    graph.add_conditional_edges("plan", route_after_plan, {"execute": "execute", "measure": "measure"})
    graph.add_edge("execute", "measure")
    graph.add_edge("measure", "learn")
    graph.add_edge("learn", "improve")
    graph.add_conditional_edges("improve", should_continue, {END: END})

    return graph.compile()


async def run_one_cycle() -> SystemState:
    """Execute a single research-to-improvement cycle."""
    workflow = build_main_workflow()
    state = _initial_state()
    final_state = await workflow.ainvoke(state)
    logger.info(
        "[Workflow] Cycle complete — opportunities: %d, approved: %d, errors: %d",
        len(final_state.get("raw_opportunities", [])),
        len(final_state.get("approved_opportunities", [])),
        len(final_state.get("errors", [])),
    )
    return final_state
