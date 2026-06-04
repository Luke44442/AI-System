"""Trend Research Agent — discovers emerging income opportunities."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.config import settings
from core.redis_client import RedisCache
from prompts.research_prompts import TREND_RESEARCH_SYSTEM, TREND_RESEARCH_PROMPT
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "best AI tools to build and sell 2025",
    "profitable micro-SaaS ideas 2025",
    "growing niche websites making money",
    "underserved B2B software opportunities",
    "trending digital products to create and sell",
    "YouTube niches with high RPM 2025",
    "newsletter business ideas growing audience",
    "automation tools demand business owners",
    "no-code tools profitable business",
    "remote income opportunities scaling",
]


class TrendResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="TrendResearchAgent",
            department="research",
            role_description=TREND_RESEARCH_SYSTEM,
            llm_temperature=0.2,
        )
        self.search_tool = WebSearchTool()
        self.system_cache = RedisCache("system")

    def get_system_prompt(self) -> str:
        return TREND_RESEARCH_SYSTEM

    async def run_cycle(self) -> None:
        logger.info("[TrendResearch] Starting research cycle")
        all_findings: List[Dict] = []

        for query in SEARCH_QUERIES[:3]:  # Limit per cycle to control API costs
            try:
                results = await self.search_tool.search(query, max_results=5)
                context = self._format_search_results(results)
                findings = await self.think_structured(
                    TREND_RESEARCH_PROMPT + f"\n\nSearch results for '{query}':\n{context}",
                    schema={
                        "trends": [
                            {
                                "name": "string",
                                "description": "string",
                                "evidence": "string",
                                "market_size": "string",
                                "income_potential": "string",
                                "time_window": "string",
                                "entry_strategy": "string",
                                "category": "string",
                            }
                        ]
                    },
                )
                all_findings.extend(findings.get("trends", []))
            except Exception as exc:
                logger.error("[TrendResearch] Search failed for '%s': %s", query, exc)

        if all_findings:
            await self._save_findings(all_findings)
            await self._forward_to_strategy(all_findings)
            await self.report_to_ceo(
                subject=f"Trend Research — {len(all_findings)} opportunities found",
                content=self._summarise_findings(all_findings),
                metadata={"findings_count": len(all_findings)},
            )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query = task.get("query", "profitable online business ideas")
        results = await self.search_tool.search(query, max_results=10)
        context = self._format_search_results(results)
        findings = await self.think_structured(
            TREND_RESEARCH_PROMPT + f"\n\nSearch context:\n{context}",
            schema={"trends": [{"name": "string", "description": "string", "income_potential": "string"}]},
        )
        return {"status": "ok", "findings": findings.get("trends", [])}

    def _format_search_results(self, results: List[Dict]) -> str:
        lines = []
        for r in results:
            lines.append(f"- {r.get('title', '')}: {r.get('snippet', '')} ({r.get('url', '')})")
        return "\n".join(lines)

    async def _save_findings(self, findings: List[Dict]) -> None:
        existing = await self.system_cache.get("research:pending_opportunities") or []
        existing.extend(findings)
        # Keep last 100
        await self.system_cache.set(
            "research:pending_opportunities",
            existing[-100:],
            ttl=settings.short_term_ttl_seconds * 24,
        )
        # Increment discovery counter
        await self.system_cache.incr("kpi:opportunities_discovered")

    async def _forward_to_strategy(self, findings: List[Dict]) -> None:
        for finding in findings[:5]:
            await self.send_message(
                recipient="StrategicPlanningAgent",
                message_type="research_finding",
                content=str(finding),
                subject=f"New Opportunity: {finding.get('name', 'Unknown')}",
                metadata={"opportunity": finding},
            )

    def _summarise_findings(self, findings: List[Dict]) -> str:
        names = [f.get("name", "?") for f in findings[:5]]
        return (
            f"Discovered {len(findings)} opportunities this cycle. "
            f"Top findings: {', '.join(names)}. "
            "Forwarded high-priority items to Strategy department."
        )
