"""Social Media Trend Agent — monitors platforms for monetisation opportunities."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.research_prompts import SOCIAL_MEDIA_TREND_PROMPT
from tools.web_search import WebSearchTool

logger = logging.getLogger(__name__)

PLATFORM_QUERIES = [
    "trending YouTube niches making money 2025",
    "viral TikTok products selling fast",
    "Twitter X creators monetising audiences",
    "Reddit communities underserved products",
    "LinkedIn B2B lead generation trends",
    "Instagram content niches high engagement",
    "Pinterest affiliate marketing opportunities",
]


class SocialMediaTrendAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SocialMediaTrendAgent",
            department="research",
            role_description=(
                "You monitor social media platforms for emerging trends, viral products, "
                "and monetisation opportunities. You identify content niches before they peak."
            ),
            llm_temperature=0.2,
        )
        self.search_tool = WebSearchTool()

    async def run_cycle(self) -> None:
        findings = []
        for query in PLATFORM_QUERIES[:2]:
            try:
                results = await self.search_tool.search(query, max_results=5)
                context = "\n".join(f"- {r.get('title')}: {r.get('snippet')}" for r in results)
                data = await self.think_structured(
                    SOCIAL_MEDIA_TREND_PROMPT + f"\n\nSearch results for '{query}':\n{context}",
                    schema={
                        "trending_opportunities": [
                            {
                                "platform": "string",
                                "trend": "string",
                                "opportunity": "string",
                                "monetisation": "string",
                                "urgency": "string",
                                "score": 0,
                            }
                        ]
                    },
                )
                findings.extend(data.get("trending_opportunities", []))
            except Exception as exc:
                logger.error("[SocialMedia] Failed: %s", exc)

        if findings:
            from core.redis_client import RedisCache
            cache = RedisCache("system")
            existing = await cache.get("research:social_trends") or []
            existing.extend(findings)
            await cache.set("research:social_trends", existing[-50:], ttl=86400 * 3)
            await self.report_to_ceo(
                subject=f"Social Media Trends — {len(findings)} opportunities",
                content=f"Found {len(findings)} social media monetisation opportunities. "
                f"Top: {findings[0].get('trend', '?') if findings else 'None'}",
                metadata={"trends": findings[:5]},
            )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        platform = task.get("platform", "all")
        results = await self.search_tool.search(
            f"trending monetisation opportunities {platform} 2025", max_results=5
        )
        context = "\n".join(f"- {r.get('snippet', '')}" for r in results)
        data = await self.think_structured(
            SOCIAL_MEDIA_TREND_PROMPT + f"\n\nContext:\n{context}",
            schema={"trending_opportunities": [{"platform": "string", "trend": "string", "score": 0}]},
        )
        return {"status": "ok", "trends": data.get("trending_opportunities", [])}
