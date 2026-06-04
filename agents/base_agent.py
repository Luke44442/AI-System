"""Abstract base class for all agents in the AI Wealth System."""
from __future__ import annotations

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import settings
from core.llm import LLMClient
from core.redis_client import RedisCache

logger = logging.getLogger(__name__)


class AgentState:
    IDLE = "idle"
    RUNNING = "running"
    BLOCKED = "blocked"
    ERROR = "error"
    STOPPED = "stopped"


class BaseAgent(ABC):
    """
    All agents inherit from this class.

    Each agent has:
    - A unique name and department
    - An LLM client for reasoning
    - A Redis cache for short-term memory and messaging
    - A task queue it processes in a loop
    """

    def __init__(
        self,
        name: str,
        department: str,
        role_description: str,
        llm_temperature: float = 0.1,
    ):
        self.agent_id = str(uuid.uuid4())
        self.name = name
        self.department = department
        self.role_description = role_description
        self.status = AgentState.IDLE
        self.current_task: Optional[str] = None
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_active: Optional[datetime] = None
        self._running = False

        self.llm = LLMClient(temperature=llm_temperature)
        self.cache = RedisCache(prefix=f"agent:{name}")
        self.global_cache = RedisCache(prefix="system")

        self._task_queue: asyncio.Queue = asyncio.Queue()
        logger.info("[%s] Initialised in department %s", name, department)

    # ── Abstract interface ─────────────────────────────────────────────────

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task and return the result dict."""

    @abstractmethod
    async def run_cycle(self) -> None:
        """Perform one autonomous work cycle (called on a schedule)."""

    def get_system_prompt(self) -> str:
        return (
            f"You are {self.name}, an autonomous AI agent in the {self.department} "
            f"department of an AI Wealth Generation System.\n\n"
            f"Role: {self.role_description}\n\n"
            "Guidelines:\n"
            "- Focus only on legal, ethical, and sustainable income opportunities.\n"
            "- Never suggest fraud, spam, hacking, or deceptive practices.\n"
            "- Be data-driven and cite sources where possible.\n"
            "- Produce concise, actionable JSON output when instructed.\n"
            "- Escalate blockers to the CEO agent immediately."
        )

    # ── Messaging ──────────────────────────────────────────────────────────

    async def send_message(
        self,
        recipient: str,
        message_type: str,
        content: str,
        subject: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> None:
        msg = {
            "id": str(uuid.uuid4()),
            "from": self.name,
            "to": recipient,
            "type": message_type,
            "subject": subject or "",
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        inbox_key = f"inbox:{recipient}"
        await self.global_cache.lpush(inbox_key, msg)
        await self.global_cache.publish(f"messages:{recipient}", msg)
        logger.debug("[%s] → [%s] (%s): %s", self.name, recipient, message_type, subject)

    async def read_inbox(self, limit: int = 20) -> List[Dict]:
        return await self.global_cache.lrange(f"inbox:{self.name}", 0, limit - 1)

    async def report_to_ceo(self, subject: str, content: str, metadata: Optional[Dict] = None) -> None:
        await self.send_message(
            recipient="SupremeAgent",
            message_type="report",
            content=content,
            subject=subject,
            metadata=metadata,
        )

    async def escalate(self, issue: str, context: Optional[Dict] = None) -> None:
        await self.send_message(
            recipient="SupremeAgent",
            message_type="escalation",
            content=issue,
            subject=f"ESCALATION from {self.name}",
            metadata=context,
        )

    # ── Task Queue ─────────────────────────────────────────────────────────

    async def enqueue_task(self, task: Dict[str, Any]) -> None:
        await self._task_queue.put(task)

    async def _process_queue(self) -> None:
        while not self._task_queue.empty():
            task = await self._task_queue.get()
            try:
                self.status = AgentState.RUNNING
                self.current_task = task.get("title", str(task))
                self.last_active = datetime.utcnow()
                result = await self.execute_task(task)
                self.tasks_completed += 1
                await self._on_task_success(task, result)
            except Exception as exc:
                self.tasks_failed += 1
                logger.error("[%s] Task failed: %s", self.name, exc, exc_info=True)
                await self._on_task_failure(task, exc)
            finally:
                self.status = AgentState.IDLE
                self.current_task = None
                self._task_queue.task_done()

    async def _on_task_success(self, task: Dict, result: Dict) -> None:
        await self.cache.set(
            f"last_result:{task.get('id', 'unknown')}",
            result,
            ttl=settings.short_term_ttl_seconds,
        )

    async def _on_task_failure(self, task: Dict, error: Exception) -> None:
        await self.escalate(
            f"Task failed: {task.get('title', '?')} — {str(error)}",
            context={"task": task},
        )

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self, cycle_interval_seconds: int = 300) -> None:
        self._running = True
        logger.info("[%s] Starting autonomous loop (interval=%ds)", self.name, cycle_interval_seconds)
        # Register in the global agent registry
        await self.global_cache.set(
            f"registry:{self.name}",
            {
                "name": self.name,
                "department": self.department,
                "status": self.status,
                "started_at": datetime.utcnow().isoformat(),
            },
        )
        while self._running:
            try:
                await self._process_queue()
                await self.run_cycle()
                await self._update_status()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("[%s] Cycle error: %s", self.name, exc, exc_info=True)
                self.status = AgentState.ERROR
            await asyncio.sleep(cycle_interval_seconds)

    async def stop(self) -> None:
        self._running = False
        self.status = AgentState.STOPPED
        logger.info("[%s] Stopped.", self.name)

    async def _update_status(self) -> None:
        await self.global_cache.set(
            f"registry:{self.name}",
            {
                "name": self.name,
                "department": self.department,
                "status": self.status,
                "tasks_completed": self.tasks_completed,
                "tasks_failed": self.tasks_failed,
                "last_active": self.last_active.isoformat() if self.last_active else None,
                "current_task": self.current_task,
            },
        )

    # ── Helpers ────────────────────────────────────────────────────────────

    async def think(self, prompt: str) -> str:
        """Simple wrapper for ad-hoc LLM reasoning."""
        return await self.llm.complete(prompt, self.get_system_prompt())

    async def think_structured(self, prompt: str, schema: Dict) -> Dict:
        """Return structured JSON output from the LLM."""
        return await self.llm.structured_output(prompt, schema, self.get_system_prompt())
