"""Unified LLM abstraction layer supporting OpenAI, Anthropic, and local models."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config import settings

logger = logging.getLogger(__name__)


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    streaming: bool = False,
) -> BaseChatModel:
    """Return a configured LangChain chat model for the given provider."""
    prov = provider or settings.primary_llm_provider

    if prov == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )

    if prov == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=model or settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=streaming,
        )

    if prov == "local":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=model or settings.local_llm_model,
            base_url=settings.local_llm_base_url,
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM provider: {prov}")


def get_embedding_model():
    """Return an embedding model appropriate for the active provider."""
    if settings.primary_llm_provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
        )
    # Fallback: local sentence-transformers (no API key required)
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


class LLMClient:
    """High-level helper wrapping the active LangChain model."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        self._llm = get_llm(provider, model, temperature, max_tokens)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        lc_messages: List[BaseMessage] = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        for m in messages:
            lc_messages.append(HumanMessage(content=m["content"]))
        response = await self._llm.ainvoke(lc_messages)
        return response.content

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return await self.chat([{"role": "user", "content": prompt}], system_prompt)

    async def structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        import json
        schema_str = json.dumps(output_schema, indent=2)
        full_prompt = (
            f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{schema_str}"
        )
        raw = await self.complete(full_prompt, system_prompt)
        # Strip markdown fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
