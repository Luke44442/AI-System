"""WebSocket endpoint for real-time dashboard updates."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.redis_client import RedisCache, get_redis

router = APIRouter()
logger = logging.getLogger(__name__)

_connections: Set[WebSocket] = set()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket):
    await websocket.accept()
    _connections.add(websocket)
    logger.info("Dashboard client connected (total: %d)", len(_connections))
    try:
        # Subscribe to all dashboard channels
        r = await get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe(
            "ai_wealth:dashboard:ceo_status",
            "ai_wealth:dashboard:finance",
            "ai_wealth:messages:SupremeAgent",
        )
        # Send initial state
        cache = RedisCache("system")
        initial = {
            "type": "init",
            "data": {
                "ceo_kpis": await cache.get("ceo:kpis") or {},
                "finance": await cache.get("finance:latest_report") or {},
                "approved_count": len(await cache.get("strategy:approved_pipeline") or []),
                "pending_count": len(await cache.get("research:pending_opportunities") or []),
            },
        }
        await websocket.send_text(json.dumps(initial))

        # Stream messages
        async def listen():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        channel = message["channel"].replace("ai_wealth:", "")
                        await websocket.send_text(
                            json.dumps({"type": "update", "channel": channel, "data": data})
                        )
                    except Exception as exc:
                        logger.debug("WS send error: %s", exc)

        # Also keep heartbeat
        async def heartbeat():
            while True:
                await asyncio.sleep(30)
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break

        tasks = [
            asyncio.create_task(listen()),
            asyncio.create_task(heartbeat()),
        ]
        # Wait for client to disconnect
        await websocket.receive_text()
        for t in tasks:
            t.cancel()
        await pubsub.unsubscribe()

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        _connections.discard(websocket)
        logger.info("Dashboard client disconnected (total: %d)", len(_connections))


async def broadcast(message: dict) -> None:
    """Broadcast a message to all connected dashboard clients."""
    dead = set()
    for ws in _connections:
        try:
            await ws.send_text(json.dumps(message))
        except Exception:
            dead.add(ws)
    _connections -= dead
