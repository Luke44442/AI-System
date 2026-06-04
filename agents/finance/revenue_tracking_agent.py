"""Revenue Tracking Agent — monitors and reports all financial activity."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from core.redis_client import RedisCache

logger = logging.getLogger(__name__)


class RevenueTrackingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="RevenueTrackingAgent",
            department="finance",
            role_description=(
                "You track all revenue and costs across every active project. "
                "You produce daily, weekly, and monthly financial summaries. "
                "You alert the CEO when milestones are hit or budgets are exceeded."
            ),
            llm_temperature=0.05,
        )
        self.system_cache = RedisCache("system")

    async def run_cycle(self) -> None:
        report = await self._generate_financial_report()
        await self.global_cache.set("finance:latest_report", report)
        await self.global_cache.publish("dashboard:finance", report)
        await self.report_to_ceo(
            subject="Financial Report",
            content=(
                f"Revenue: ${report.get('total_revenue_usd', 0):.2f} | "
                f"Costs: ${report.get('total_costs_usd', 0):.2f} | "
                f"Profit: ${report.get('net_profit_usd', 0):.2f}"
            ),
            metadata={"report": report},
        )

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        task_type = task.get("type", "report")
        if task_type == "record_revenue":
            await self._record_entry(task.get("amount", 0), "revenue", task.get("source", ""))
            return {"status": "ok", "recorded": task.get("amount")}
        if task_type == "record_cost":
            await self._record_entry(task.get("amount", 0), "cost", task.get("source", ""))
            return {"status": "ok", "recorded": task.get("amount")}
        report = await self._generate_financial_report()
        return {"status": "ok", "report": report}

    async def _record_entry(self, amount: float, entry_type: str, source: str) -> None:
        entries = await self.system_cache.get("finance:entries") or []
        entries.append(
            {
                "amount": amount,
                "type": entry_type,
                "source": source,
                "recorded_at": datetime.utcnow().isoformat(),
            }
        )
        await self.system_cache.set("finance:entries", entries[-500:], ttl=86400 * 30)
        # Update running totals
        if entry_type == "revenue":
            current = float(await self.system_cache.get("kpi:total_revenue_usd") or 0)
            await self.system_cache.set("kpi:total_revenue_usd", current + amount)
        else:
            current = float(await self.system_cache.get("kpi:total_costs_usd") or 0)
            await self.system_cache.set("kpi:total_costs_usd", current + amount)

    async def _generate_financial_report(self) -> Dict:
        total_revenue = float(await self.system_cache.get("kpi:total_revenue_usd") or 0)
        total_costs = float(await self.system_cache.get("kpi:total_costs_usd") or 0)
        entries: List[Dict] = await self.system_cache.get("finance:entries") or []
        recent_revenue = sum(
            e["amount"] for e in entries[-30:] if e.get("type") == "revenue"
        )
        return {
            "total_revenue_usd": total_revenue,
            "total_costs_usd": total_costs,
            "net_profit_usd": total_revenue - total_costs,
            "roi_pct": ((total_revenue - total_costs) / max(total_costs, 1)) * 100,
            "recent_revenue_30_entries": recent_revenue,
            "active_projects": len(await self.system_cache.get("strategy:approved_pipeline") or []),
            "generated_at": datetime.utcnow().isoformat(),
        }
