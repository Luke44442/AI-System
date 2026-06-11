"""Structured system event recording.

One call, two sinks: a structlog line (for log aggregation) and a row in
`system_events` (for the failures dashboard and order lifecycle timelines).
Recording an event must never break the calling flow — a failure to write
the row is logged and swallowed.
"""
from __future__ import annotations
import uuid
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fulfillment import SystemEvent

log = structlog.get_logger("system_events")

SEVERITIES = ("info", "warning", "error", "critical")


async def record_event(
    db: AsyncSession,
    event_type: str,
    *,
    severity: str = "info",
    message: Optional[str] = None,
    payload: Optional[dict] = None,
    order_id: Optional[uuid.UUID] = None,
    listing_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
) -> Optional[SystemEvent]:
    """Persist a system event and emit a structured log line.

    Does NOT commit — the caller owns the transaction, so events land
    atomically with the state change they describe.
    """
    if severity not in SEVERITIES:
        severity = "info"

    logger = {
        "info": log.info, "warning": log.warning,
        "error": log.error, "critical": log.critical,
    }[severity]
    logger(
        event_type,
        message=message,
        order_id=str(order_id) if order_id else None,
        listing_id=str(listing_id) if listing_id else None,
        product_id=str(product_id) if product_id else None,
        **(payload or {}),
    )

    try:
        event = SystemEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            payload=payload or {},
            order_id=order_id,
            listing_id=listing_id,
            product_id=product_id,
        )
        db.add(event)
        return event
    except Exception as exc:  # pragma: no cover - defensive
        log.error("system_event_write_failed", event_type=event_type, error=str(exc))
        return None
