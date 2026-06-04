"""Unified memory manager — coordinates short-term (Redis) and long-term (vector) memory."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import settings
from core.redis_client import RedisCache
from core.vector_store import VectorMemory

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Single interface to all memory subsystems.

    Short-term:  Redis (fast, TTL-based)
    Long-term:   PostgreSQL (structured) + ChromaDB (semantic search)
    """

    def __init__(self, scope: str = "global"):
        self.scope = scope
        self.short_term = RedisCache(f"memory:{scope}")
        self.vector = VectorMemory(f"longterm_{scope}")

    # ── Short-term ─────────────────────────────────────────────────

    async def remember(self, key: str, value: Any, ttl: int = settings.short_term_ttl_seconds) -> None:
        await self.short_term.set(key, value, ttl=ttl)

    async def recall(self, key: str) -> Optional[Any]:
        return await self.short_term.get(key)

    async def forget(self, key: str) -> None:
        await self.short_term.delete(key)

    # ── Long-term vector memory ─────────────────────────────────────

    async def store_knowledge(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict] = None,
    ) -> None:
        """Store a piece of knowledge in the vector DB for semantic retrieval."""
        try:
            await self.vector.upsert(doc_id, text, metadata or {})
            logger.debug("[Memory] Stored knowledge: %s", doc_id)
        except Exception as exc:
            logger.warning("[Memory] Vector store unavailable, using Redis fallback: %s", exc)
            cache = RedisCache("system")
            existing = await cache.get("knowledge:fallback") or []
            existing.append({"id": doc_id, "text": text, "metadata": metadata or {}, "stored_at": datetime.utcnow().isoformat()})
            await cache.set("knowledge:fallback", existing[-500:], ttl=86400 * settings.long_term_retention_days)

    async def search_knowledge(
        self,
        query: str,
        n_results: int = settings.max_vector_results,
        where: Optional[Dict] = None,
    ) -> List[Dict]:
        """Semantic search over stored knowledge."""
        try:
            return await self.vector.query(query, n_results=n_results, where=where)
        except Exception as exc:
            logger.warning("[Memory] Vector search failed, using fallback: %s", exc)
            return await self._fallback_search(query, n_results)

    async def _fallback_search(self, query: str, n_results: int) -> List[Dict]:
        cache = RedisCache("system")
        entries = await cache.get("knowledge:fallback") or []
        query_lower = query.lower()
        matches = [e for e in entries if query_lower in (e.get("text", "") + str(e.get("metadata", ""))).lower()]
        return matches[:n_results]

    # ── Composite helpers ──────────────────────────────────────────

    async def store_lesson(self, title: str, description: str, tags: List[str] = None) -> str:
        doc_id = f"lesson_{datetime.utcnow().timestamp()}"
        text = f"LESSON: {title}\n{description}"
        await self.store_knowledge(doc_id, text, {"type": "lesson", "title": title, "tags": tags or []})
        # Also cache in short-term for immediate access
        lessons = await self.recall("recent_lessons") or []
        lessons.append({"id": doc_id, "title": title, "description": description, "tags": tags or []})
        await self.remember("recent_lessons", lessons[-20:])
        return doc_id

    async def find_similar_opportunities(self, opportunity_desc: str) -> List[Dict]:
        return await self.search_knowledge(opportunity_desc, n_results=5, where={"type": "opportunity"})
