"""Web search tool with DuckDuckGo (free), Serper, and Google backends."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings

logger = logging.getLogger(__name__)


class WebSearchTool:
    """Unified web search with automatic provider fallback."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.default_search_provider

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=5))
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            if self.provider == "serper" and settings.serper_api_key:
                return await self._search_serper(query, max_results)
            if self.provider == "google" and settings.google_search_api_key:
                return await self._search_google(query, max_results)
            return await self._search_duckduckgo(query, max_results)
        except Exception as exc:
            logger.warning("[WebSearch] Provider %s failed, falling back: %s", self.provider, exc)
            return await self._search_duckduckgo(query, max_results)

    async def _search_duckduckgo(self, query: str, max_results: int) -> List[Dict]:
        try:
            from duckduckgo_search import DDGS
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results)),
            )
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                }
                for r in results
            ]
        except Exception as exc:
            logger.error("[WebSearch] DuckDuckGo failed: %s", exc)
            return self._mock_results(query)

    async def _search_serper(self, query: str, max_results: int) -> List[Dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": settings.serper_api_key,
                    "Content-Type": "application/json",
                },
                json={"q": query, "num": max_results},
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                }
                for r in data.get("organic", [])[:max_results]
            ]

    async def _search_google(self, query: str, max_results: int) -> List[Dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_search_api_key,
                    "cx": settings.google_search_engine_id,
                    "q": query,
                    "num": min(max_results, 10),
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                }
                for item in data.get("items", [])[:max_results]
            ]

    def _mock_results(self, query: str) -> List[Dict]:
        """Return placeholder results when all search providers fail."""
        return [
            {
                "title": f"Search result for: {query}",
                "url": "https://example.com",
                "snippet": "Search provider unavailable. Configure SERPER_API_KEY or GOOGLE_SEARCH_API_KEY for reliable results.",
            }
        ]
