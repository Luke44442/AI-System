"""Message protocol definitions for inter-agent communication."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
import uuid
from datetime import datetime


class MessageType(str, Enum):
    # Reports
    REPORT              = "report"
    ESCALATION          = "escalation"
    # Directives
    DIRECTIVE           = "directive"
    TASK_ASSIGN         = "task_assign"
    EXECUTE             = "execute"
    # Research
    RESEARCH_FINDING    = "research_finding"
    QUALIFIED_OPP       = "qualified_opportunities"
    COMPETITOR_RESULT   = "competitor_analysis_result"
    MARKET_RESULT       = "market_analysis_result"
    # Strategy
    SCORE_RESULT        = "score_result"
    RISK_RESULT         = "risk_analysis_result"
    VALIDATION_RESULT   = "validation_result"
    BUSINESS_MODEL      = "business_model_result"
    APPROVAL_REQUEST    = "opportunity_for_approval"
    # Execution
    CONTENT_REQUEST     = "create_content"
    CONTENT_READY       = "content_ready"
    OUTREACH_REQUEST    = "outreach_request"
    OUTREACH_READY      = "outreach_ready"
    SALES_COPY_REQUEST  = "sales_copy_request"
    SALES_COPY_READY    = "sales_copy_ready"
    MARKETING_REQUEST   = "marketing_request"
    WEBSITE_BUILD       = "build_website"
    # Finance
    REVENUE_UPDATE      = "revenue_update"
    COST_ALERT          = "cost_alert"
    # Self-improvement
    NEW_LESSONS         = "new_lessons"
    IMPROVE_SUGGESTION  = "improvement_suggestion"
    PROMPT_IMPROVE      = "prompt_improve"


class Priority(int, Enum):
    LOW      = 1
    NORMAL   = 5
    HIGH     = 8
    CRITICAL = 10


def build_message(
    sender: str,
    recipient: str,
    msg_type: MessageType,
    content: str,
    subject: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    priority: Priority = Priority.NORMAL,
) -> Dict[str, Any]:
    return {
        "id":        str(uuid.uuid4()),
        "from":      sender,
        "to":        recipient,
        "type":      msg_type.value,
        "subject":   subject or "",
        "content":   content,
        "metadata":  metadata or {},
        "priority":  priority.value,
        "timestamp": datetime.utcnow().isoformat(),
    }
