"""Strategic Planning Agent — converts opportunities into execution plans."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.config import settings
from core.redis_client import RedisCache
from prompts.strategy_prompts import (
    STRATEGIC_PLANNING_SYSTEM,
    OPPORTUNITY_SCORING_PROMPT,
    EXECUTION_PLAN_PROMPT,
)
from scoring.opportunity_scorer import OpportunityScorer

logger = logging.getLogger(__name__)


class StrategicPlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="StrategicPlanningAgent",
            department="strategy",
            role_description=STRATEGIC_PLANNING_SYSTEM,
            llm_temperature=0.05,
        )
        self.scorer = OpportunityScorer()
        self.system_cache = RedisCache("system")

    def get_system_prompt(self) -> str:
        return STRATEGIC_PLANNING_SYSTEM

    async def run_cycle(self) -> None:
        # Process qualified opportunities from inbox
        inbox = await self.read_inbox(limit=20)
        for msg in inbox:
            if msg.get("type") in ("qualified_opportunities", "research_finding"):
                opps = msg.get("metadata", {}).get("opportunities", [])
                if not opps and msg.get("metadata", {}).get("opportunity"):
                    opps = [msg["metadata"]["opportunity"]]
                for opp in opps:
                    await self._score_and_route(opp)

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        scored = await self._score_opportunity(opp)
        if scored["overall_score"] >= settings.opportunity_score_threshold:
            plan = await self._create_execution_plan(scored)
            return {"status": "approved", "opportunity": scored, "plan": plan}
        return {"status": "rejected", "opportunity": scored}

    async def _score_and_route(self, raw_opp: Dict) -> None:
        try:
            scored = await self._score_opportunity(raw_opp)
            if scored["overall_score"] >= settings.opportunity_score_threshold:
                plan = await self._create_execution_plan(scored)
                scored["execution_plan"] = plan
                # Send to CEO for final approval
                await self.send_message(
                    recipient="SupremeAgent",
                    message_type="opportunity_for_approval",
                    content=f"High-score opportunity ready for approval: {scored.get('title', '?')} "
                    f"(score: {scored['overall_score']:.1f})",
                    subject=f"Approval Request: {scored.get('title', '?')}",
                    metadata={"opportunity": scored},
                )
                # Also save to pipeline
                pipeline = await self.system_cache.get("strategy:approved_pipeline") or []
                pipeline.append(scored)
                await self.system_cache.set("strategy:approved_pipeline", pipeline[-20:], ttl=86400 * 14)
            else:
                logger.info(
                    "[Strategy] Rejected '%s' (score: %.1f)",
                    raw_opp.get("name", "?"),
                    scored["overall_score"],
                )
        except Exception as exc:
            logger.error("[Strategy] Scoring failed: %s", exc)

    async def _score_opportunity(self, raw_opp: Dict) -> Dict:
        title = raw_opp.get("name", raw_opp.get("title", "Unknown"))
        desc = raw_opp.get("description", str(raw_opp))
        category = raw_opp.get("category", "online business")

        scored_raw = await self.think_structured(
            OPPORTUNITY_SCORING_PROMPT.format(
                title=title,
                description=desc,
                category=category,
                market_data=raw_opp.get("market_data", "Not available"),
            ),
            schema={
                "profit_potential": 0,
                "difficulty": 0,
                "startup_cost": 0,
                "time_required": 0,
                "automation_potential": 0,
                "scalability": 0,
                "risk_level": 0,
                "estimated_monthly_revenue_usd": 0.0,
                "estimated_startup_cost_usd": 0.0,
                "time_to_first_revenue_days": 0,
                "overall_score": 0.0,
                "recommendation": "string",
                "reasoning": "string",
            },
        )
        scored_raw["title"] = title
        scored_raw["description"] = desc
        scored_raw["category"] = category
        scored_raw["original"] = raw_opp

        # Use our own weighted formula as a sanity check
        computed_score = self.scorer.compute_score(scored_raw)
        scored_raw["overall_score"] = computed_score
        return scored_raw

    async def _create_execution_plan(self, opportunity: Dict) -> Dict:
        return await self.think_structured(
            EXECUTION_PLAN_PROMPT.format(
                opportunity=opportunity.get("title", "?"),
                budget=settings.max_execution_budget_usd,
                timeline_weeks=8,
            ),
            schema={
                "phases": [
                    {
                        "name": "string",
                        "weeks": "string",
                        "tasks": [{"task": "string", "department": "string", "hours": 0}],
                    }
                ],
                "kpis": ["string"],
                "first_revenue_milestone": "string",
                "total_budget_usd": 0.0,
            },
        )
