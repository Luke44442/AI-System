"""Automation Builder Agent — creates automation systems for approved projects."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent
from prompts.execution_prompts import AUTOMATION_BLUEPRINT_PROMPT

logger = logging.getLogger(__name__)


class AutomationBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="AutomationBuilderAgent",
            department="execution",
            role_description=(
                "You design and build automation systems using Python, APIs, n8n, and no-code tools. "
                "Your goal is to make every approved business run with minimal human intervention. "
                "You write clean, well-documented automation code and workflows."
            ),
            llm_temperature=0.1,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "execute":
                meta = msg.get("metadata", {})
                opp = meta.get("opportunity", {})
                if opp:
                    blueprint = await self._create_automation(opp)
                    await self.report_to_ceo(
                        subject=f"Automation Blueprint Ready: {opp.get('title', '?')}",
                        content=f"Built automation blueprint for {opp.get('title', '?')}. "
                        f"Estimated time savings: {blueprint.get('estimated_hours_saved_weekly', 0)}h/week.",
                        metadata={"blueprint": blueprint, "opportunity": opp},
                    )
                    # Trigger marketing
                    await self.send_message(
                        recipient="MarketingAgent",
                        message_type="execute",
                        content=f"Launch marketing for: {opp.get('title', '?')}",
                        metadata={"opportunity": opp},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        blueprint = await self._create_automation(opp)
        return {"status": "ok", "automation_blueprint": blueprint}

    async def _create_automation(self, opportunity: Dict) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        plan = opportunity.get("execution_plan", {})
        return await self.think_structured(
            AUTOMATION_BLUEPRINT_PROMPT.format(
                process=f"Running {name} business operations",
                tools="Python, FastAPI, Redis, PostgreSQL, n8n, Zapier, OpenAI API",
                goal="Automate 80%+ of daily operations",
            )
            + f"\n\nExecution plan context: {str(plan)[:500]}",
            schema={
                "automation_steps": [
                    {
                        "step": "string",
                        "tool": "string",
                        "trigger": "string",
                        "action": "string",
                        "output": "string",
                    }
                ],
                "tech_stack": ["string"],
                "estimated_hours_saved_weekly": 0,
                "implementation_time_days": 0,
                "automation_coverage_pct": 0,
                "code_snippets": [{"filename": "string", "description": "string", "code": "string"}],
            },
        )
