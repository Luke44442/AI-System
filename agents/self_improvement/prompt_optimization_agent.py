"""Prompt Optimisation Agent — continuously improves agent prompts."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache
from prompts.improvement_prompts import PROMPT_OPTIMIZATION_PROMPT

logger = logging.getLogger(__name__)


class PromptOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="PromptOptimizationAgent",
            department="self_improvement",
            role_description=(
                "You analyse agent performance data and systematically improve prompts "
                "to get better, more consistent outputs. You use A/B testing methodology "
                "and track improvement metrics."
            ),
            llm_temperature=0.1,
        )
        self.system_cache = RedisCache("system")

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "improvement_suggestion":
                lesson = msg.get("metadata", {}).get("lesson", {})
                if lesson.get("recommended_action"):
                    await self._log_improvement_suggestion(lesson)

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        agent_name = task.get("agent_name", "unknown")
        current_prompt = task.get("current_prompt", "")
        issues = task.get("issues", "")
        good_outputs = task.get("good_outputs", "")
        bad_outputs = task.get("bad_outputs", "")
        optimised = await self.think_structured(
            PROMPT_OPTIMIZATION_PROMPT.format(
                current_prompt=current_prompt,
                agent_name=agent_name,
                issues=issues,
                good_outputs=good_outputs,
                bad_outputs=bad_outputs,
            ),
            schema={
                "revised_prompt": "string",
                "change_summary": "string",
                "changes_made": ["string"],
                "expected_improvement": "string",
                "version": "string",
            },
        )
        # Store the improved prompt
        prompts = await self.system_cache.get("optimised_prompts") or {}
        prompts[agent_name] = optimised
        await self.system_cache.set("optimised_prompts", prompts, ttl=86400 * 30)
        return {"status": "ok", "optimised_prompt": optimised}

    async def _log_improvement_suggestion(self, lesson: Dict) -> None:
        suggestions = await self.system_cache.get("prompt_improvement_queue") or []
        suggestions.append(lesson)
        await self.system_cache.set("prompt_improvement_queue", suggestions[-50:], ttl=86400 * 7)
