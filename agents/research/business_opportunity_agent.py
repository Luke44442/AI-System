"""Business Opportunity Agent — evaluates and qualifies opportunities."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.research_prompts import MARKET_ANALYSIS_PROMPT
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class BusinessOpportunityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BusinessOpportunityAgent",
            department="research",
            role_description=(
                "You evaluate raw opportunity ideas and qualify them based on profitability, "
                "scalability, and automation potential. You filter noise from signal."
            ),
            llm_temperature=0.15,
        )
        self.search_tool = WebSearchTool()

    async def run_cycle(self) -> None:
        from core.redis_client import RedisCache
        cache = RedisCache("system")
        pending = await cache.get("research:pending_opportunities") or []
        if not pending:
            return
        # Qualify top 5 pending opportunities
        to_qualify = pending[:5]
        remaining = pending[5:]
        qualified = []
        for raw_opp in to_qualify:
            try:
                qualified_opp = await self._qualify_opportunity(raw_opp)
                if qualified_opp.get("qualified"):
                    qualified.append(qualified_opp)
            except Exception as exc:
                logger.error("[BusinessOpportunity] Qualification failed: %s", exc)
        await cache.set(
            "research:pending_opportunities",
            remaining,
            ttl=86400,
        )
        if qualified:
            existing = await cache.get("research:qualified_opportunities") or []
            existing.extend(qualified)
            await cache.set("research:qualified_opportunities", existing[-50:], ttl=86400 * 7)
            await self.send_message(
                recipient="StrategicPlanningAgent",
                message_type="qualified_opportunities",
                content=f"Qualified {len(qualified)} opportunities",
                metadata={"opportunities": qualified},
            )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        result = await self._qualify_opportunity(opp)
        return {"status": "ok", "qualified_opportunity": result}

    async def _qualify_opportunity(self, raw_opp: Dict) -> Dict:
        name = raw_opp.get("name", raw_opp.get("title", "Unknown"))
        description = raw_opp.get("description", "")
        search = await self.search_tool.search(f"{name} legitimate business revenue proof", max_results=3)
        evidence = "\n".join(f"- {r.get('snippet', '')}" for r in search)
        result = await self.think_structured(
            f"""Evaluate this business opportunity for qualification:

Name: {name}
Description: {description}
Evidence from web: {evidence}

Assess:
1. Is there real market demand? (evidence of people buying/paying)
2. Is this legal and ethical?
3. Can this generate $1000+/month realistically?
4. Can it be automated to run with <4 hours/week?
5. Is the barrier to entry low enough for a bootstrapped start?

Return your qualification decision as JSON.""",
            schema={
                "qualified": True,
                "confidence": 0.0,
                "reasoning": "string",
                "estimated_monthly_revenue": "string",
                "automation_score": 0,
                "legal_check": True,
                "quick_wins": ["string"],
                "risks": ["string"],
                "name": "string",
                "description": "string",
                "category": "string",
            },
        )
        result["name"] = name
        result["original"] = raw_opp
        return result
