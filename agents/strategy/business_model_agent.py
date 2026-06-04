"""Business Model Agent — designs optimal monetisation models."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.strategy_prompts import BUSINESS_MODEL_PROMPT

logger = logging.getLogger(__name__)


class BusinessModelAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="BusinessModelAgent",
            department="strategy",
            role_description=(
                "You design optimal business models and monetisation strategies for each "
                "approved opportunity. You focus on unit economics, pricing psychology, "
                "and the fastest path to sustainable revenue."
            ),
            llm_temperature=0.1,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "design_business_model":
                opp = msg.get("metadata", {}).get("opportunity", {})
                if opp:
                    model = await self._design_model(opp)
                    await self.send_message(
                        recipient="StrategicPlanningAgent",
                        message_type="business_model_result",
                        content=str(model),
                        metadata={"business_model": model},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        model = await self._design_model(opp)
        return {"status": "ok", "business_model": model}

    async def _design_model(self, opportunity: Dict) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            BUSINESS_MODEL_PROMPT.format(
                opportunity=name,
                market=opportunity.get("category", "online"),
            ),
            schema={
                "revenue_model": "string",
                "pricing_tiers": [{"name": "string", "price_usd": 0, "features": ["string"]}],
                "customer_acquisition": {
                    "primary_channel": "string",
                    "secondary_channels": ["string"],
                    "estimated_cac_usd": 0,
                },
                "unit_economics": {
                    "ltv_usd": 0,
                    "cac_usd": 0,
                    "ltv_cac_ratio": 0,
                    "gross_margin_pct": 0,
                },
                "mvp_definition": "string",
                "revenue_milestones": {
                    "month_1": 0,
                    "month_3": 0,
                    "month_6": 0,
                    "month_12": 0,
                },
            },
        )
