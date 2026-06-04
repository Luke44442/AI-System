"""
Autonomous scheduler — runs research cycles and CEO reviews on configurable intervals.
Start: python -m scheduler
"""
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


async def research_cycle_job():
    logger.info("[Scheduler] Starting scheduled research cycle at %s", datetime.utcnow().isoformat())
    try:
        from workflows.main_loop import run_one_cycle
        result = await run_one_cycle()
        logger.info(
            "[Scheduler] Cycle complete — discovered: %d, approved: %d",
            len(result.get("raw_opportunities", [])),
            len(result.get("approved_opportunities", [])),
        )
    except Exception as exc:
        logger.error("[Scheduler] Cycle failed: %s", exc, exc_info=True)


async def ceo_review_job():
    logger.info("[Scheduler] CEO review at %s", datetime.utcnow().isoformat())
    try:
        from agents.ceo.supreme_agent import SupremeAgent
        ceo = SupremeAgent()
        await ceo.run_cycle()
    except Exception as exc:
        logger.error("[Scheduler] CEO review failed: %s", exc, exc_info=True)


async def finance_job():
    try:
        from agents.finance.revenue_tracking_agent import RevenueTrackingAgent
        agent = RevenueTrackingAgent()
        await agent.run_cycle()
    except Exception as exc:
        logger.error("[Scheduler] Finance job failed: %s", exc, exc_info=True)


async def self_improvement_job():
    try:
        from agents.self_improvement.learning_agent import LearningAgent
        from agents.self_improvement.workflow_optimization_agent import WorkflowOptimizationAgent
        await LearningAgent().run_cycle()
        await WorkflowOptimizationAgent().run_cycle()
    except Exception as exc:
        logger.error("[Scheduler] Self-improvement job failed: %s", exc, exc_info=True)


async def run_scheduler():
    from core.config import settings
    research_interval = settings.research_loop_interval_minutes * 60
    ceo_interval      = settings.ceo_review_interval_minutes * 60

    logger.info(
        "[Scheduler] Starting — research every %dm, CEO review every %dm",
        settings.research_loop_interval_minutes,
        settings.ceo_review_interval_minutes,
    )

    last_research = 0.0
    last_ceo      = 0.0
    last_finance  = 0.0
    last_improve  = 0.0

    while True:
        now = asyncio.get_event_loop().time()
        if now - last_research >= research_interval:
            asyncio.create_task(research_cycle_job())
            last_research = now
        if now - last_ceo >= ceo_interval:
            asyncio.create_task(ceo_review_job())
            last_ceo = now
        if now - last_finance >= 3600:
            asyncio.create_task(finance_job())
            last_finance = now
        if now - last_improve >= 7200:
            asyncio.create_task(self_improvement_job())
            last_improve = now
        await asyncio.sleep(60)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_scheduler())
