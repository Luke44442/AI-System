"""Marketing Agent — designs and executes growth marketing strategies."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.execution_prompts import MARKETING_STRATEGY_PROMPT

logger = logging.getLogger(__name__)


class MarketingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MarketingAgent",
            department="execution",
            role_description=(
                "You design and execute growth marketing strategies for approved opportunities. "
                "You focus on organic growth, SEO, content marketing, and cost-effective "
                "paid acquisition. You measure everything and double down on what works."
            ),
            llm_temperature=0.2,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") in ("execute", "marketing_request"):
                meta = msg.get("metadata", {})
                opp = meta.get("opportunity", {})
                if opp:
                    strategy = await self._create_marketing_strategy(opp)
                    await self.send_message(
                        recipient="ContentAgent",
                        message_type="create_content",
                        content=f"Create marketing content for: {opp.get('title', '?')}",
                        metadata={
                            "opportunity": opp,
                            "content_type": "landing_page",
                            "platform": "website",
                            "audience": strategy.get("target_audience", "general"),
                            "goal": "conversions",
                        },
                    )
                    await self.report_to_ceo(
                        subject=f"Marketing Strategy Ready: {opp.get('title', '?')}",
                        content=str(strategy)[:500],
                        metadata={"strategy": strategy},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        budget = task.get("monthly_budget", 500)
        target_revenue = task.get("target_revenue", 5000)
        strategy = await self._create_marketing_strategy(opp, budget, target_revenue)
        return {"status": "ok", "marketing_strategy": strategy}

    async def _create_marketing_strategy(
        self,
        opportunity: Dict,
        monthly_budget: float = 500,
        target_revenue: float = 5000,
    ) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            MARKETING_STRATEGY_PROMPT.format(
                opportunity=name,
                monthly_budget=monthly_budget,
                target_revenue=target_revenue,
            ),
            schema={
                "target_audience": "string",
                "positioning_statement": "string",
                "seo_strategy": {
                    "primary_keywords": ["string"],
                    "content_calendar_topics": ["string"],
                },
                "social_strategy": {
                    "platforms": ["string"],
                    "content_types": ["string"],
                    "posting_frequency": "string",
                },
                "email_strategy": {
                    "lead_magnet": "string",
                    "sequence_length": 0,
                },
                "month_1_actions": ["string"],
                "estimated_organic_reach_month_3": 0,
                "expected_leads_month_1": 0,
            },
        )
