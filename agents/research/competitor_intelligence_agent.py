"""Competitor Intelligence Agent — maps the competitive landscape."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.research_prompts import COMPETITOR_INTELLIGENCE_PROMPT
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)


class CompetitorIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CompetitorIntelligenceAgent",
            department="research",
            role_description=(
                "You research and map competitors for each business opportunity. "
                "You identify market gaps, weaknesses, and positioning opportunities."
            ),
            llm_temperature=0.1,
        )
        self.search_tool = WebSearchTool()

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "competitor_research":
                opp = msg.get("metadata", {}).get("opportunity", {})
                if opp:
                    analysis = await self._research_competitors(opp)
                    await self.send_message(
                        recipient="StrategicPlanningAgent",
                        message_type="competitor_analysis_result",
                        content=str(analysis),
                        subject=f"Competitor Intel: {opp.get('name', '?')}",
                        metadata={"analysis": analysis},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        result = await self._research_competitors(opp)
        return {"status": "ok", "competitor_analysis": result}

    async def _research_competitors(self, opportunity: Dict) -> Dict:
        name = opportunity.get("name", opportunity.get("title", "Unknown"))
        category = opportunity.get("category", "online business")
        results = await self.search_tool.search(
            f"top competitors {name} {category} alternatives", max_results=8
        )
        context = "\n".join(
            f"- {r.get('title')}: {r.get('snippet')} ({r.get('url', '')})"
            for r in results
        )
        return await self.think_structured(
            COMPETITOR_INTELLIGENCE_PROMPT.format(
                opportunity=name, category=category
            )
            + f"\n\nSearch findings:\n{context}",
            schema={
                "competitors": [
                    {
                        "name": "string",
                        "url": "string",
                        "estimated_revenue": "string",
                        "strengths": ["string"],
                        "weaknesses": ["string"],
                        "pricing": "string",
                    }
                ],
                "market_gap": "string",
                "positioning_recommendation": "string",
                "differentiation_strategies": ["string"],
            },
        )
