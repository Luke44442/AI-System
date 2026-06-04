"""Market Analysis Agent — deep dives into specific markets."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from prompts.research_prompts import MARKET_ANALYSIS_PROMPT
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class MarketAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="MarketAnalysisAgent",
            department="research",
            role_description=(
                "You perform deep market analysis on specific business opportunities. "
                "You assess TAM, competition, customer pain points, and monetisation models."
            ),
            llm_temperature=0.1,
        )
        self.search_tool = WebSearchTool()

    async def run_cycle(self) -> None:
        # Read inbox for opportunities that need market analysis
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "analyze_market":
                opp = msg.get("metadata", {}).get("opportunity", {})
                if opp:
                    analysis = await self._analyse_market(opp)
                    await self.send_message(
                        recipient=msg.get("from", "StrategicPlanningAgent"),
                        message_type="market_analysis_result",
                        content=str(analysis),
                        subject=f"Market Analysis: {opp.get('name', '?')}",
                        metadata={"analysis": analysis, "opportunity": opp},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opportunity = task.get("opportunity", {})
        analysis = await self._analyse_market(opportunity)
        return {"status": "ok", "analysis": analysis}

    async def _analyse_market(self, opportunity: Dict) -> Dict:
        name = opportunity.get("name", opportunity.get("title", "Unknown"))
        search_results = await self.search_tool.search(
            f"{name} market size revenue potential 2025", max_results=5
        )
        context = "\n".join(
            f"- {r.get('title')}: {r.get('snippet')}" for r in search_results
        )
        return await self.think_structured(
            MARKET_ANALYSIS_PROMPT.format(opportunity=name)
            + f"\n\nResearch context:\n{context}",
            schema={
                "tam_estimate": "string",
                "growth_rate": "string",
                "top_competitors": ["string"],
                "customer_pain_points": ["string"],
                "best_monetisation_model": "string",
                "recommended_price_point": "string",
                "distribution_channels": ["string"],
                "barriers_to_entry": ["string"],
                "market_trend": "string",
                "verdict": "string",
            },
        )
