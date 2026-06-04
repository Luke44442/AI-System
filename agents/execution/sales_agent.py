"""Sales Agent — handles sales copy, funnels, and conversion optimisation."""
from __future__ import annotations

import logging
from typing import Any, Dict

from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class SalesAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="SalesAgent",
            department="execution",
            role_description=(
                "You craft compelling sales copy, design conversion funnels, and optimise "
                "for maximum revenue per visitor. You understand persuasion psychology, "
                "A/B testing, and sales funnel optimisation."
            ),
            llm_temperature=0.3,
        )

    async def run_cycle(self) -> None:
        inbox = await self.read_inbox(limit=10)
        for msg in inbox:
            if msg.get("type") == "sales_copy_request":
                meta = msg.get("metadata", {})
                copy = await self._create_sales_copy(meta.get("opportunity", {}))
                await self.send_message(
                    recipient=msg.get("from", "MarketingAgent"),
                    message_type="sales_copy_ready",
                    content=str(copy),
                    metadata={"sales_copy": copy},
                )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        copy = await self._create_sales_copy(task.get("opportunity", {}))
        return {"status": "ok", "sales_copy": copy}

    async def _create_sales_copy(self, opportunity: Dict) -> Dict:
        name = opportunity.get("title", opportunity.get("name", "Unknown"))
        return await self.think_structured(
            f"""Create complete sales copy for this product/service:

Product/Service: {name}
Description: {opportunity.get('description', '')}
Target Price: ${opportunity.get('estimated_startup_cost_usd', 97)}/month
Target Audience: {opportunity.get('category', 'business owners')}

Create:
1. Hero section headline and subheadline
2. Problem statement (agitate the pain)
3. Solution presentation
4. Key features and benefits (feature → benefit format)
5. Social proof placeholder text
6. Objection handling (top 5 objections + rebuttals)
7. Pricing section copy
8. CTA button text (3 variations)
9. Urgency/scarcity element
10. Money-back guarantee text

Return as structured JSON.""",
            schema={
                "headline": "string",
                "subheadline": "string",
                "problem_statement": "string",
                "solution_intro": "string",
                "features_benefits": [{"feature": "string", "benefit": "string"}],
                "objection_rebuttals": [{"objection": "string", "rebuttal": "string"}],
                "cta_variants": ["string"],
                "pricing_copy": "string",
                "guarantee_text": "string",
            },
        )
