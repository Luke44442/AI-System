"""ChromaDB vector store client for semantic memory."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from core.config import settings
from core.llm import get_embedding_model

logger = logging.getLogger(__name__)

_chroma_client: Optional[chromadb.AsyncHttpClient] = None


async def get_chroma() -> chromadb.AsyncHttpClient:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = await chromadb.AsyncHttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma_client


class VectorMemory:
    """Async wrapper around a ChromaDB collection."""

    def __init__(self, collection_name: str):
        self.collection_name = (
            f"{settings.chroma_collection_prefix}_{collection_name}"
        )
        self._collection = None
        self._embedder = get_embedding_model()

    async def _get_collection(self):
        if self._collection is None:
            client = await get_chroma()
            self._collection = await client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _embed(self, texts: List[str]) -> List[List[float]]:
        return self._embedder.embed_documents(texts)

    async def upsert(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        col = await self._get_collection()
        embeddings = self._embed([text])
        await col.upsert(
            ids=[doc_id],
            embeddings=embeddings,
            documents=[text],
            metadatas=[metadata or {}],
        )

    async def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        col = await self._get_collection()
        query_embedding = self._embedder.embed_query(query_text)
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        results = await col.query(**kwargs)
        output = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        dists = results["distances"][0]
        for doc_id, doc, meta, dist in zip(ids, docs, metas, dists):
            output.append(
                {
                    "id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "similarity": 1 - dist,
                }
            )
        return output

    async def delete(self, doc_id: str) -> None:
        col = await self._get_collection()
        await col.delete(ids=[doc_id])

    async def count(self) -> int:
        col = await self._get_collection()
        return await col.count()
