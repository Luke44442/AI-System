"""Risk Analysis Agent — assesses and mitigates execution risk."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.strategy_prompts import RISK_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class RiskAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="RiskAnalysisAgent",
            department="strategy",
            role_description=(
                "You perform thorough risk analysis on every business opportunity before "
                "execution. You identify legal, financial, operational, and market risks "
                "and provide clear mitigation strategies."
            ),
            llm_temperature=0.05,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "risk_analysis_request":
                opp = msg.get("metadata", {}).get("opportunity", {})
                plan = msg.get("metadata", {}).get("plan", {})
                analysis = await self._analyse_risk(opp, plan)
                await self.send_message(
                    recipient=msg.get("from", "StrategicPlanningAgent"),
                    message_type="risk_analysis_result",
                    content=str(analysis),
                    subject=f"Risk Analysis: {opp.get('title', '?')}",
                    metadata={"risk_analysis": analysis},
                )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        plan = task.get("plan", {})
        analysis = await self._analyse_risk(opp, plan)
        return {"status": "ok", "risk_analysis": analysis}

    async def _analyse_risk(self, opportunity: Dict, plan: Dict) -> Dict:
        return await self.think_structured(
            RISK_ANALYSIS_PROMPT.format(
                opportunity=str(opportunity),
                plan=str(plan),
            ),
            schema={
                "risks": [
                    {
                        "name": "string",
                        "category": "string",
                        "probability": "string",
                        "impact": "string",
                        "score": 0,
                        "mitigation": "string",
                        "contingency": "string",
                    }
                ],
                "overall_risk_rating": "string",
                "go_no_go": "string",
                "top_concern": "string",
                "risk_summary": "string",
            },
        )
