"""Profit Optimisation Agent — maximises margins across all projects."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache

logger = logging.getLogger(__name__)


class ProfitOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ProfitOptimizationAgent",
            department="finance",
            role_description=(
                "You analyse revenue and cost data to identify profit maximisation opportunities. "
                "You recommend pricing changes, upsell strategies, cost cuts, and "
                "revenue diversification."
            ),
            llm_temperature=0.1,
        )
        self.system_cache = RedisCache("system")

    async def run_cycle(self) -> None:
        report = await self.system_cache.get("finance:latest_report") or {}
        if not report:
            return
        optimisations = await self._generate_optimisations(report)
        await self.global_cache.set("finance:optimisations", optimisations)
        await self.report_to_ceo(
            subject="Profit Optimisation Recommendations",
            content=str(optimisations)[:500],
            metadata={"optimisations": optimisations},
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        report = task.get("financial_report", {})
        optimisations = await self._generate_optimisations(report)
        return {"status": "ok", "optimisations": optimisations}

    async def _generate_optimisations(self, report: Dict) -> Dict:
        return await self.think_structured(
            f"""Analyse this financial data and recommend profit optimisations.

Financial Report:
- Total Revenue: ${report.get('total_revenue_usd', 0):.2f}
- Total Costs: ${report.get('total_costs_usd', 0):.2f}
- Net Profit: ${report.get('net_profit_usd', 0):.2f}
- ROI: {report.get('roi_pct', 0):.1f}%
- Active Projects: {report.get('active_projects', 0)}

Recommend:
1. Revenue increase strategies (upsell, pricing, new streams)
2. Cost reduction opportunities
3. Highest-ROI activities to double down on
4. Activities to cut or pause
5. Next 30-day profit target""",
            schema={
                "revenue_increase_strategies": ["string"],
                "cost_reduction_actions": ["string"],
                "top_roi_activities": ["string"],
                "activities_to_cut": ["string"],
                "30_day_profit_target_usd": 0.0,
                "expected_margin_improvement_pct": 0.0,
                "priority_action": "string",
            },
        )
