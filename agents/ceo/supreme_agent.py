"""Supreme Agent — CEO of the AI Wealth System."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.base_agent import BaseAgent
from core.config import settings
from core.redis_client import RedisCache
from prompts.ceo_prompts import (
    CEO_SYSTEM_PROMPT,
    OBJECTIVE_SETTING_PROMPT,
    PERFORMANCE_REVIEW_PROMPT,
    CONFLICT_RESOLUTION_PROMPT,
)

logger = logging.getLogger(__name__)

DEPARTMENTS = ["research", "strategy", "execution", "finance", "self_improvement"]

DEPARTMENT_HEADS = {
    "research": "TrendResearchAgent",
    "strategy": "StrategicPlanningAgent",
    "execution": "AutomationBuilderAgent",
    "finance": "RevenueTrackingAgent",
    "self_improvement": "KnowledgeManagementAgent",
}


class SupremeAgent(BaseAgent):
    """
    The CEO agent. Orchestrates all departments, sets objectives,
    reviews KPIs, resolves conflicts, and maintains global strategy.
    """

    def __init__(self):
        super().__init__(
            name="SupremeAgent",
            department="executive",
            role_description=CEO_SYSTEM_PROMPT,
            llm_temperature=0.05,
        )
        self.global_objectives: List[str] = [
            "Identify and validate 3+ high-score online income opportunities per week",
            "Maintain research pipeline with 20+ opportunities at scoring stage",
            "Achieve positive ROI on first execution within 90 days",
            "Continuously improve agent performance and prompt quality",
        ]
        self.kpis: Dict[str, Any] = {}
        self.active_projects: List[Dict] = []

    def get_system_prompt(self) -> str:
        return CEO_SYSTEM_PROMPT

    # ── Core cycle ─────────────────────────────────────────────────────────

    async def run_cycle(self) -> None:
        logger.info("[CEO] Starting review cycle")
        inbox = await self.read_inbox(limit=50)
        reports = [m for m in inbox if m.get("type") == "report"]
        escalations = [m for m in inbox if m.get("type") == "escalation"]

        await self._process_escalations(escalations)
        await self._review_department_reports(reports)
        await self._update_kpis()
        await self._set_next_objectives()
        await self._broadcast_status()
        logger.info("[CEO] Review cycle complete — KPIs: %s", self.kpis)

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "generic")
        if task_type == "set_objective":
            return await self._handle_set_objective(task)
        if task_type == "approve_opportunity":
            return await self._handle_approve_opportunity(task)
        if task_type == "resolve_conflict":
            return await self._handle_resolve_conflict(task)
        return {"status": "ok", "message": f"CEO processed: {task_type}"}

    # ── Internal handlers ──────────────────────────────────────────────────

    async def _process_escalations(self, escalations: List[Dict]) -> None:
        for esc in escalations:
            logger.warning("[CEO] Escalation from %s: %s", esc.get("from"), esc.get("subject"))
            resolution = await self.think(
                CONFLICT_RESOLUTION_PROMPT.format(
                    escalation=esc.get("content", ""),
                    agent=esc.get("from", "unknown"),
                )
            )
            await self.send_message(
                recipient=esc.get("from", ""),
                message_type="directive",
                content=resolution,
                subject=f"Resolution: {esc.get('subject', '')}",
            )

    async def _review_department_reports(self, reports: List[Dict]) -> None:
        if not reports:
            return
        combined = "\n\n".join(
            f"FROM {r['from']}:\n{r['content']}" for r in reports[:10]
        )
        review = await self.think(
            PERFORMANCE_REVIEW_PROMPT.format(
                reports=combined,
                objectives="\n".join(self.global_objectives),
            )
        )
        await self.global_cache.set(
            "ceo:latest_review",
            {"review": review, "timestamp": datetime.utcnow().isoformat()},
            ttl=settings.short_term_ttl_seconds * 2,
        )

    async def _update_kpis(self) -> None:
        cache = RedisCache("system")
        opportunities_raw = await cache.get("kpi:opportunities_discovered") or 0
        revenue_raw = await cache.get("kpi:total_revenue_usd") or 0.0
        agents_active = 0
        for name in await self._get_all_agent_names():
            info = await cache.get(f"registry:{name}")
            if info and info.get("status") not in ("stopped", "error"):
                agents_active += 1

        self.kpis = {
            "opportunities_discovered": int(opportunities_raw),
            "total_revenue_usd": float(revenue_raw),
            "agents_active": agents_active,
            "objectives_count": len(self.global_objectives),
            "active_projects": len(self.active_projects),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.global_cache.set("ceo:kpis", self.kpis)

    async def _set_next_objectives(self) -> None:
        kpi_summary = str(self.kpis)
        new_objectives_raw = await self.think_structured(
            OBJECTIVE_SETTING_PROMPT.format(
                current_objectives="\n".join(self.global_objectives),
                kpis=kpi_summary,
            ),
            schema={
                "revised_objectives": ["string"],
                "new_directives": [{"department": "string", "directive": "string"}],
                "priority_focus": "string",
            },
        )
        if "revised_objectives" in new_objectives_raw:
            self.global_objectives = new_objectives_raw["revised_objectives"]
        for directive in new_objectives_raw.get("new_directives", []):
            dept = directive.get("department", "")
            head = DEPARTMENT_HEADS.get(dept)
            if head:
                await self.send_message(
                    recipient=head,
                    message_type="directive",
                    content=directive["directive"],
                    subject=f"CEO Directive — {dept.title()} Department",
                )

    async def _broadcast_status(self) -> None:
        status = {
            "agent": self.name,
            "kpis": self.kpis,
            "objectives": self.global_objectives,
            "active_projects": self.active_projects,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.global_cache.publish("dashboard:ceo_status", status)

    async def _get_all_agent_names(self) -> List[str]:
        return [
            "TrendResearchAgent",
            "BusinessOpportunityAgent",
            "MarketAnalysisAgent",
            "CompetitorIntelligenceAgent",
            "SocialMediaTrendAgent",
            "StrategicPlanningAgent",
            "BusinessModelAgent",
            "RiskAnalysisAgent",
            "ValidationAgent",
            "AutomationBuilderAgent",
            "WebsiteBuilderAgent",
            "MarketingAgent",
            "SalesAgent",
            "ContentAgent",
            "OutreachAgent",
            "RevenueTrackingAgent",
            "CostAnalysisAgent",
            "ProfitOptimizationAgent",
            "KnowledgeManagementAgent",
            "LearningAgent",
            "PromptOptimizationAgent",
            "WorkflowOptimizationAgent",
        ]

    async def _handle_set_objective(self, task: Dict) -> Dict:
        self.global_objectives.append(task["objective"])
        return {"status": "ok", "objectives": self.global_objectives}

    async def _handle_approve_opportunity(self, task: Dict) -> Dict:
        opp = task.get("opportunity", {})
        score = opp.get("overall_score", 0)
        approved = score >= settings.opportunity_score_threshold
        if approved:
            self.active_projects.append(opp)
            await self.send_message(
                recipient="AutomationBuilderAgent",
                message_type="execute",
                content=f"Execute approved opportunity: {opp.get('title')}",
                subject="New Execution Task",
                metadata={"opportunity": opp},
            )
        return {"status": "approved" if approved else "rejected", "score": score}

    async def _handle_resolve_conflict(self, task: Dict) -> Dict:
        resolution = await self.think(
            CONFLICT_RESOLUTION_PROMPT.format(
                escalation=task.get("conflict", ""),
                agent=task.get("from", "unknown"),
            )
        )
        return {"status": "resolved", "resolution": resolution}

    def get_dashboard_data(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "kpis": self.kpis,
            "objectives": self.global_objectives,
            "active_projects": self.active_projects,
            "tasks_completed": self.tasks_completed,
            "last_active": self.last_active.isoformat() if self.last_active else None,
        }
