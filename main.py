#!/usr/bin/env python3
"""
AI Wealth System — Main Entry Point
Run: python main.py [--mode api|worker|cycle|all]
"""
import argparse
import asyncio
import logging
import sys

import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(colors=True),
    ]
)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)


def run_api():
    import uvicorn
    from core.config import settings
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


async def run_cycle_once():
    from workflows.main_loop import run_one_cycle
    print("═" * 60)
    print("  AI WEALTH SYSTEM — Running one research cycle")
    print("═" * 60)
    final = await run_one_cycle()
    print(f"\n✓ Cycle complete")
    print(f"  Opportunities discovered : {len(final.get('raw_opportunities', []))}")
    print(f"  Qualified                : {len(final.get('qualified_opportunities', []))}")
    print(f"  Approved                 : {len(final.get('approved_opportunities', []))}")
    print(f"  Errors                   : {len(final.get('errors', []))}")
    if final.get("errors"):
        print(f"\n  Errors:")
        for e in final["errors"]:
            print(f"    - {e}")


async def run_continuous():
    """Run cycles indefinitely on a schedule."""
    from core.config import settings
    interval = settings.research_loop_interval_minutes * 60
    print(f"Starting continuous operation (interval: {settings.research_loop_interval_minutes}m)")
    while True:
        try:
            await run_cycle_once()
        except Exception as exc:
            logging.error("Cycle failed: %s", exc, exc_info=True)
        await asyncio.sleep(interval)


async def run_all():
    """Start API + continuous cycle runner concurrently."""
    import uvicorn
    from core.config import settings
    config = uvicorn.Config(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await asyncio.gather(
        server.serve(),
        run_continuous(),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Wealth System")
    parser.add_argument(
        "--mode",
        choices=["api", "cycle", "continuous", "all"],
        default="api",
        help="Run mode",
    )
    args = parser.parse_args()

    if args.mode == "api":
        run_api()
    elif args.mode == "cycle":
        asyncio.run(run_cycle_once())
    elif args.mode == "continuous":
        asyncio.run(run_continuous())
    elif args.mode == "all":
        asyncio.run(run_all())
