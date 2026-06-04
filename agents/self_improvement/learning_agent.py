"""Learning Agent — extracts lessons from outcomes and improves the system."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache
from prompts.improvement_prompts import LEARNING_AGENT_SYSTEM, LESSON_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class LearningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="LearningAgent",
            department="self_improvement",
            role_description=LEARNING_AGENT_SYSTEM,
            llm_temperature=0.1,
        )
        self.system_cache = RedisCache("system")

    def get_system_prompt(self) -> str:
        return LEARNING_AGENT_SYSTEM

    async def run_cycle(self) -> None:
        # Collect recent agent activity data
        activity_log = await self.system_cache.get("activity:recent_log") or []
        outcomes = {
            "approved_opportunities": len(await self.system_cache.get("strategy:approved_pipeline") or []),
            "total_revenue": await self.system_cache.get("kpi:total_revenue_usd") or 0,
            "opportunities_discovered": await self.system_cache.get("kpi:opportunities_discovered") or 0,
        }
        if not activity_log:
            return
        lessons = await self._extract_lessons(activity_log, outcomes)
        # Store lessons
        existing = await self.system_cache.get("learning:lessons") or []
        existing.extend(lessons.get("lessons", []))
        await self.system_cache.set("learning:lessons", existing[-200:], ttl=86400 * 30)
        # Forward important lessons to knowledge management
        await self.send_message(
            recipient="KnowledgeManagementAgent",
            message_type="new_lessons",
            content=f"Extracted {len(lessons.get('lessons', []))} lessons",
            metadata={"lessons": lessons},
        )
        # Forward prompt improvement suggestions
        for lesson in lessons.get("lessons", []):
            if lesson.get("category") == "improvement" and lesson.get("confidence", 0) >= 7:
                await self.send_message(
                    recipient="PromptOptimizationAgent",
                    message_type="improvement_suggestion",
                    content=str(lesson),
                    metadata={"lesson": lesson},
                )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        activity = task.get("activity_data", [])
        outcomes = task.get("outcomes", {})
        lessons = await self._extract_lessons(activity, outcomes)
        return {"status": "ok", "lessons": lessons}

    async def _extract_lessons(self, activity_data: list, outcomes: Dict) -> Dict:
        return await self.think_structured(
            LESSON_EXTRACTION_PROMPT.format(
                activity_data=str(activity_data)[:2000],
                outcomes=str(outcomes),
            ),
            schema={
                "lessons": [
                    {
                        "category": "string",
                        "title": "string",
                        "description": "string",
                        "recommended_action": "string",
                        "confidence": 0,
                        "priority": 0,
                    }
                ],
                "success_patterns": ["string"],
                "failure_patterns": ["string"],
                "summary": "string",
            },
        )
