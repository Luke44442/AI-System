"""Cost Analysis Agent — monitors and optimises spending."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache

logger = logging.getLogger(__name__)


class CostAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CostAnalysisAgent",
            department="finance",
            role_description=(
                "You monitor all system and project costs, identify overspending, "
                "and recommend cost optimisations. You track API usage, infrastructure, "
                "and execution costs."
            ),
            llm_temperature=0.05,
        )
        self.system_cache = RedisCache("system")

    async def run_cycle(self) -> None:
        analysis = await self._analyse_costs()
        await self.global_cache.set("finance:cost_analysis", analysis)
        if analysis.get("budget_exceeded"):
            await self.escalate(
                f"Budget limit approached! Current spend: ${analysis.get('total_costs_usd', 0):.2f}",
                context=analysis,
            )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        analysis = await self._analyse_costs()
        return {"status": "ok", "cost_analysis": analysis}

    async def _analyse_costs(self) -> Dict:
        total_costs = float(await self.system_cache.get("kpi:total_costs_usd") or 0)
        budget_limit = 50.0
        return await self.think_structured(
            f"""Analyse the current cost structure and provide optimisation recommendations.

Total costs to date: ${total_costs:.2f}
Budget limit: ${budget_limit:.2f}
Budget utilisation: {(total_costs/budget_limit)*100:.1f}%

Provide:
1. Cost breakdown by category
2. Areas of overspending
3. Immediate cost reduction actions
4. Long-term cost optimisation strategies
5. Budget recommendations for next cycle""",
            schema={
                "total_costs_usd": total_costs,
                "budget_limit_usd": budget_limit,
                "budget_utilisation_pct": round((total_costs / budget_limit) * 100, 1),
                "budget_exceeded": total_costs >= budget_limit * 0.9,
                "cost_categories": [{"category": "string", "amount_usd": 0, "pct": 0}],
                "optimisation_actions": ["string"],
                "projected_monthly_cost": 0.0,
                "recommendation": "string",
            },
        )
