"""Content Agent — produces all written and creative assets."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.execution_prompts import CONTENT_AGENT_SYSTEM, CONTENT_CREATION_PROMPT

logger = logging.getLogger(__name__)


class ContentAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="ContentAgent",
            department="execution",
            role_description=CONTENT_AGENT_SYSTEM,
            llm_temperature=0.7,  # Higher for creative output
        )

    def get_system_prompt(self) -> str:
        return CONTENT_AGENT_SYSTEM

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "create_content":
                meta = msg.get("metadata", {})
                content = await self._create_content(
                    opportunity=meta.get("opportunity", {}),
                    content_type=meta.get("content_type", "blog_post"),
                    platform=meta.get("platform", "website"),
                    audience=meta.get("audience", "general"),
                    goal=meta.get("goal", "drive traffic and conversions"),
                )
                await self.send_message(
                    recipient=msg.get("from", "MarketingAgent"),
                    message_type="content_ready",
                    content=str(content),
                    subject=f"Content ready: {meta.get('content_type', '?')}",
                    metadata={"content": content},
                )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        content = await self._create_content(
            opportunity=task.get("opportunity", {}),
            content_type=task.get("content_type", "blog_post"),
            platform=task.get("platform", "website"),
            audience=task.get("audience", "general"),
            goal=task.get("goal", "drive conversions"),
        )
        return {"status": "ok", "content": content}

    async def _create_content(
        self,
        opportunity: Dict,
        content_type: str,
        platform: str,
        audience: str,
        goal: str,
    ) -> Dict:
        opp_name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            CONTENT_CREATION_PROMPT.format(
                opportunity=opp_name,
                content_type=content_type,
                audience=audience,
                platform=platform,
                goal=goal,
            ),
            schema={
                "content_type": content_type,
                "platform": platform,
                "headline": "string",
                "headline_variants": ["string"],
                "body": "string",
                "call_to_action": "string",
                "seo_keywords": ["string"],
                "word_count": 0,
                "estimated_read_time_minutes": 0,
                "meta_description": "string",
            },
        )
