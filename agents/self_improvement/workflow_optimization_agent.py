"""Workflow Optimisation Agent — improves agent coordination and efficiency."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache
from prompts.improvement_prompts import WORKFLOW_OPTIMIZATION_PROMPT

logger = logging.getLogger(__name__)


class WorkflowOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="WorkflowOptimizationAgent",
            department="self_improvement",
            role_description=(
                "You analyse agent workflows and identify bottlenecks, inefficiencies, "
                "and coordination failures. You propose and implement workflow improvements "
                "to increase throughput and reduce errors."
            ),
            llm_temperature=0.1,
        )
        self.system_cache = RedisCache("system")

    async def run_cycle(self) -> None:
        metrics = await self._collect_workflow_metrics()
        if metrics:
            optimisations = await self._optimise_workflows(metrics)
            await self.global_cache.set("workflow:optimisations", optimisations)
            await self.report_to_ceo(
                subject="Workflow Optimisation Report",
                content=str(optimisations)[:400],
                metadata={"optimisations": optimisations},
            )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        metrics = await self._collect_workflow_metrics()
        result = await self._optimise_workflows(metrics)
        return {"status": "ok", "optimisations": result}

    async def _collect_workflow_metrics(self) -> Dict:
        all_agent_names = [
            "TrendResearchAgent", "BusinessOpportunityAgent", "MarketAnalysisAgent",
            "StrategicPlanningAgent", "ValidationAgent", "AutomationBuilderAgent",
            "MarketingAgent", "ContentAgent", "RevenueTrackingAgent",
        ]
        agents_data = []
        for name in all_agent_names:
            info = await self.global_cache.get(f"registry:{name}")
            if info:
                agents_data.append(info)
        return {
            "agents": agents_data,
            "opportunities_discovered": await self.system_cache.get("kpi:opportunities_discovered") or 0,
            "pipeline_count": len(await self.system_cache.get("strategy:approved_pipeline") or []),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _optimise_workflows(self, metrics: Dict) -> Dict:
        idle_agents = [
            a["name"] for a in metrics.get("agents", []) if a.get("status") == "idle"
        ]
        error_agents = [
            a["name"] for a in metrics.get("agents", []) if a.get("status") == "error"
        ]
        return await self.think_structured(
            WORKFLOW_OPTIMIZATION_PROMPT.format(
                workflow_name="Main Research-to-Revenue Pipeline",
                avg_time="Unknown",
                success_rate=75,
                failures=f"Error agents: {error_agents}",
                utilisation=f"Idle agents: {idle_agents}",
            ),
            schema={
                "bottlenecks": ["string"],
                "parallelisation_opportunities": ["string"],
                "agent_reassignments": [{"agent": "string", "new_task": "string"}],
                "estimated_throughput_improvement_pct": 0,
                "priority_fix": "string",
            },
        )
