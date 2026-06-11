"""Marketplace listing state machine — retry/backoff/dead-letter transitions.

Runs `_apply_result` against a stub listing and a mock session: no DB, no
network. This protects the guarantee that marketplace failures are never
silent — every failure either schedules a retry or lands in the dead-letter
table with a critical event.
"""
from __future__ import annotations

import asyncio
import types
from decimal import Decimal
from unittest.mock import MagicMock

from app.models.fulfillment import MarketplaceDeadLetter, SystemEvent
from app.services.marketplaces.base import ListingState, ProductPayload, SyncResult, SyncStatus
from app.services.marketplaces.service import _apply_result, _backoff_minutes


def make_listing(**overrides):
    base = dict(
        id="22222222-2222-2222-2222-222222222222",
        product_id="11111111-1111-1111-1111-111111111111",
        platform="etsy",
        status=ListingState.CREATED.value,
        listing_id=None,
        listing_url=None,
        title=None,
        price=None,
        quantity=0,
        sync_error=None,
        sync_attempts=0,
        last_synced_at=None,
        next_sync_at=None,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def make_payload() -> ProductPayload:
    return ProductPayload(
        id="11111111-1111-1111-1111-111111111111", sku="TF-OUD-100",
        title="Tom Ford Oud Wood", description="d", price=Decimal("310"), quantity=5,
    )


def apply(listing, result, db=None):
    db = db or MagicMock()
    asyncio.run(_apply_result(db, listing, result, make_payload(), "create"))
    return db


def test_success_publishes_and_resets_retry_state():
    listing = make_listing(sync_attempts=3, status=ListingState.RETRYING.value,
                           next_sync_at="2026-01-01T00:00:00")
    apply(listing, SyncResult("etsy", SyncStatus.SUCCESS, listing_id="42",
                              listing_url="https://etsy.com/listing/42"))
    assert listing.status == ListingState.PUBLISHED.value
    assert listing.listing_id == "42"
    assert listing.sync_attempts == 0
    assert listing.next_sync_at is None
    assert listing.sync_error is None


def test_partial_success_emits_warning_event():
    listing = make_listing()
    db = apply(listing, SyncResult("etsy", SyncStatus.SUCCESS, listing_id="42",
                                   message="image upload failed"))
    events = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], SystemEvent)]
    assert any(e.event_type == "marketplace_sync_warning" for e in events)
    assert listing.status == ListingState.PUBLISHED.value


def test_skipped_marks_pending_credentials():
    listing = make_listing()
    apply(listing, SyncResult("etsy", SyncStatus.SKIPPED, message="not configured"))
    assert listing.status == ListingState.PENDING.value
    assert listing.sync_attempts == 0


def test_failure_schedules_retry_with_backoff():
    listing = make_listing()
    db = apply(listing, SyncResult("etsy", SyncStatus.FAILED, message="boom"))
    assert listing.status == ListingState.RETRYING.value
    assert listing.sync_attempts == 1
    assert listing.next_sync_at is not None
    events = [c.args[0] for c in db.add.call_args_list if isinstance(c.args[0], SystemEvent)]
    assert any(e.event_type == "marketplace_sync_failed" and e.severity == "error" for e in events)


def test_backoff_is_exponential():
    assert _backoff_minutes(1) == 5
    assert _backoff_minutes(2) == 10
    assert _backoff_minutes(3) == 20
    assert _backoff_minutes(5) == 80


def test_exhausted_retries_dead_letter():
    from app.config import settings
    listing = make_listing(sync_attempts=settings.MARKETPLACE_MAX_SYNC_ATTEMPTS - 1)
    db = apply(listing, SyncResult("etsy", SyncStatus.FAILED, message="still broken"))
    assert listing.status == ListingState.DEAD.value
    added = [c.args[0] for c in db.add.call_args_list]
    dead_letters = [a for a in added if isinstance(a, MarketplaceDeadLetter)]
    assert len(dead_letters) == 1
    assert dead_letters[0].platform == "etsy"
    events = [a for a in added if isinstance(a, SystemEvent)]
    assert any(e.severity == "critical" for e in events)
