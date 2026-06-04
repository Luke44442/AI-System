"""Outreach Agent — manages customer acquisition and partnerships."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.execution_prompts import OUTREACH_PROMPT

logger = logging.getLogger(__name__)


class OutreachAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="OutreachAgent",
            department="execution",
            role_description=(
                "You create ethical, value-first outreach strategies and templates for "
                "acquiring customers and building partnerships. You NEVER spam. "
                "You focus on personalised, permission-based outreach that delivers genuine value."
            ),
            llm_temperature=0.3,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "outreach_request":
                meta = msg.get("metadata", {})
                strategy = await self._create_outreach_strategy(
                    meta.get("opportunity", {}),
                    meta.get("target_audience", "business owners"),
                    meta.get("goal", "acquire first 10 customers"),
                )
                await self.send_message(
                    recipient=msg.get("from", "MarketingAgent"),
                    message_type="outreach_ready",
                    content=str(strategy),
                    metadata={"outreach_strategy": strategy},
                )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        strategy = await self._create_outreach_strategy(
            task.get("opportunity", {}),
            task.get("target_audience", "business owners"),
            task.get("goal", "acquire first 10 customers"),
        )
        return {"status": "ok", "outreach_strategy": strategy}

    async def _create_outreach_strategy(
        self,
        opportunity: Dict,
        target_audience: str,
        goal: str,
    ) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            OUTREACH_PROMPT.format(
                opportunity=name,
                target_audience=target_audience,
                goal=goal,
            ),
            schema={
                "icp": {
                    "description": "string",
                    "company_size": "string",
                    "pain_points": ["string"],
                },
                "channels": ["string"],
                "templates": [
                    {
                        "channel": "string",
                        "subject": "string",
                        "body": "string",
                        "follow_up": "string",
                    }
                ],
                "daily_volume": 0,
                "expected_response_rate_pct": 0,
                "compliance_notes": ["string"],
            },
        )
