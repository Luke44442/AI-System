"""Website Builder Agent — generates website plans and starter code."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class WebsiteBuilderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="WebsiteBuilderAgent",
            department="execution",
            role_description=(
                "You plan and scaffold websites for approved business opportunities. "
                "You produce technology recommendations, site architecture, and starter code. "
                "You favour fast, lightweight setups: Next.js, Astro, or plain HTML+CSS."
            ),
            llm_temperature=0.15,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "build_website":
                meta = msg.get("metadata", {})
                opp = meta.get("opportunity", {})
                if opp:
                    plan = await self._plan_website(opp)
                    await self.send_message(
                        recipient="AutomationBuilderAgent",
                        message_type="website_plan_ready",
                        content=str(plan),
                        metadata={"website_plan": plan, "opportunity": opp},
                    )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        opp = task.get("opportunity", {})
        plan = await self._plan_website(opp)
        return {"status": "ok", "website_plan": plan}

    async def _plan_website(self, opportunity: Dict) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            f"""Plan a website for this business:

Business: {name}
Description: {opportunity.get('description', '')}
Revenue Model: {opportunity.get('business_model', 'SaaS')}
Budget: Low (< $50/month)

Design a complete website plan:
1. Page structure (pages needed)
2. Technology stack recommendation
3. Hosting recommendation with cost
4. Key sections for each page
5. Required integrations (payments, email, analytics)
6. SEO setup checklist
7. Time to launch estimate
8. Estimated monthly running cost""",
            schema={
                "pages": [{"name": "string", "purpose": "string", "key_sections": ["string"]}],
                "tech_stack": "string",
                "framework": "string",
                "hosting": "string",
                "monthly_cost_usd": 0,
                "integrations": ["string"],
                "seo_checklist": ["string"],
                "time_to_launch_days": 0,
                "domain_suggestions": ["string"],
            },
        )
