"""Validation Agent — validates opportunities with lightweight market tests."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ValidationAgent",
            department="strategy",
            role_description=(
                "You validate business opportunities by searching for real customer demand, "
                "proof of purchase intent, and evidence that similar businesses are succeeding. "
                "You design minimal validation experiments."
            ),
            llm_temperature=0.1,
        )
        self.search_tool = WebSearchTool()

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "validate":
                opp = msg.get("metadata", {}).get("opportunity", {})
                if opp:
                    validation = await self._validate(opp)
                    await self.send_message(
                        recipient=msg.get("from", "StrategicPlanningAgent"),
                        message_type="validation_result",
                        content=str(validation),
                        metadata={"validation": validation, "opportunity": opp},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        result = await self._validate(opp)
        return {"status": "ok", "validation": result}

    async def _validate(self, opportunity: Dict) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        signals = await self.search_tool.search(
            f'"{name}" "buy" OR "paying" OR "customers" OR "revenue" site:reddit.com OR site:indiehackers.com',
            max_results=5,
        )
        context = "\n".join(f"- {r.get('snippet', '')}" for r in signals)
        return await self.think_structured(
            f"""Validate this business opportunity using the market signals below.

Opportunity: {name}
Description: {opportunity.get('description', '')}

Market signals found:
{context}

Assess:
1. Demand evidence (are people actively seeking this?)
2. Payment willingness (are people paying for similar things?)
3. Competition proof (are others successfully selling this?)
4. Risk red flags (any signals this won't work?)
5. Validation experiment design (cheapest way to test in 1 week)""",
            schema={
                "demand_score": 0,
                "payment_willingness_score": 0,
                "competition_proof_score": 0,
                "overall_validation_score": 0,
                "validated": True,
                "red_flags": ["string"],
                "positive_signals": ["string"],
                "validation_experiment": {
                    "method": "string",
                    "time_days": 0,
                    "cost_usd": 0,
                    "success_criteria": "string",
                },
            },
        )
