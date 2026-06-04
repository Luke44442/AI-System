"""Redis client singleton with async support."""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from core.config import settings

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


class RedisCache:
    """Thin helper over raw Redis commands for JSON-serialised values."""

    def __init__(self, prefix: str = "ai_wealth"):
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        r = await get_redis()
        serialised = json.dumps(value)
        if ttl:
            await r.setex(self._key(key), ttl, serialised)
        else:
            await r.set(self._key(key), serialised)

    async def get(self, key: str) -> Optional[Any]:
        r = await get_redis()
        raw = await r.get(self._key(key))
        if raw is None:
            return None
        return json.loads(raw)

    async def delete(self, key: str) -> None:
        r = await get_redis()
        await r.delete(self._key(key))

    async def exists(self, key: str) -> bool:
        r = await get_redis()
        return bool(await r.exists(self._key(key)))

    async def incr(self, key: str) -> int:
        r = await get_redis()
        return await r.incr(self._key(key))

    async def lpush(self, key: str, *values: Any) -> None:
        r = await get_redis()
        serialised = [json.dumps(v) for v in values]
        await r.lpush(self._key(key), *serialised)

    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        r = await get_redis()
        raw_list = await r.lrange(self._key(key), start, end)
        return [json.loads(x) for x in raw_list]

    async def publish(self, channel: str, message: Any) -> None:
        r = await get_redis()
        await r.publish(f"{self.prefix}:{channel}", json.dumps(message))

    async def subscribe(self, *channels: str):
        r = await get_redis()
        pubsub = r.pubsub()
        prefixed = [f"{self.prefix}:{c}" for c in channels]
        await pubsub.subscribe(*prefixed)
        return pubsub
