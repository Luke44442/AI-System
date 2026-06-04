"""SQLAlchemy ORM models for the AI Wealth System."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


# ─── Agents ──────────────────────────────────────────────────────────────────

class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="idle")  # idle|running|blocked|error
    current_task: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tasks_completed: Mapped[int] = mapped_column(Integer, default=0)
    tasks_failed: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    config: Mapped[Dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    messages: Mapped[list["AgentMessage"]] = relationship(back_populates="agent")
    tasks: Mapped[list["Task"]] = relationship(back_populates="agent")


# ─── Tasks ────────────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    agent_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("agents.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_task_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("tasks.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agent: Mapped[Optional[Agent]] = relationship(back_populates="tasks")


# ─── Opportunities ────────────────────────────────────────────────────────────

class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    source_agent: Mapped[str] = mapped_column(String(100), nullable=False)

    # Scoring dimensions (0-100)
    profit_potential: Mapped[int] = mapped_column(Integer, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, default=50)
    startup_cost: Mapped[int] = mapped_column(Integer, default=50)
    time_required: Mapped[int] = mapped_column(Integer, default=50)
    automation_potential: Mapped[int] = mapped_column(Integer, default=0)
    scalability: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[int] = mapped_column(Integer, default=50)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)

    status: Mapped[str] = mapped_column(
        String(30), default="discovered"
    )  # discovered|analyzed|approved|executing|completed|rejected
    estimated_monthly_revenue: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_startup_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_size: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    competition_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    raw_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    execution_plan: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    revenue_entries: Mapped[list["RevenueEntry"]] = relationship(
        back_populates="opportunity"
    )


# ─── Revenue ──────────────────────────────────────────────────────────────────

class RevenueEntry(Base):
    __tablename__ = "revenue_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    opportunity_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("opportunities.id"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    amount_usd: Mapped[float] = mapped_column(Float, nullable=False)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)  # revenue|cost
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    opportunity: Mapped[Optional[Opportunity]] = relationship(
        back_populates="revenue_entries"
    )


# ─── Agent Messages ───────────────────────────────────────────────────────────

class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"), nullable=False)
    sender: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(100), nullable=False)
    message_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    agent: Mapped[Agent] = relationship(back_populates="messages")


# ─── Memory / Knowledge ───────────────────────────────────────────────────────

class MemoryEntry(Base):
    __tablename__ = "memory_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    memory_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # fact|lesson|strategy|pattern
    scope: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # global|department:X|agent:X
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5)  # 1-10
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    vector_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ─── Research Reports ─────────────────────────────────────────────────────────

class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    findings: Mapped[Dict] = mapped_column(JSON, default=dict)
    opportunities_found: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


# ─── System KPIs ──────────────────────────────────────────────────────────────

class SystemKPI(Base):
    __tablename__ = "system_kpis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_unit: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    period: Mapped[str] = mapped_column(String(20), default="daily")
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
