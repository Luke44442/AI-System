-- ===========================================================================
-- Migration 007: Supplier fulfillment + observability layer
--   * supplier_orders          — guaranteed terminal state for every paid order
--   * system_events            — structured event log (order/supplier/marketplace)
--   * marketplace_dead_letters — listings that exhausted retry budget
--   * marketplace_listings     — retry bookkeeping column
-- Idempotent.
-- ===========================================================================

CREATE TABLE IF NOT EXISTS supplier_orders (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id          UUID NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    supplier_id       UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    status            VARCHAR(30) NOT NULL DEFAULT 'pending',
    external_order_id VARCHAR(255),
    external_status   VARCHAR(100),
    tracking_number   VARCHAR(255),
    carrier           VARCHAR(100),
    tracking_url      TEXT,
    failure_reason    TEXT,
    queued_reason     TEXT,
    attempts          INTEGER NOT NULL DEFAULT 0,
    last_attempt_at   TIMESTAMPTZ,
    request_payload   JSONB DEFAULT '{}',
    response_payload  JSONB DEFAULT '{}',
    resolved_by       VARCHAR(320),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_supplier_orders_status      ON supplier_orders(status);
CREATE INDEX IF NOT EXISTS ix_supplier_orders_supplier_id ON supplier_orders(supplier_id);
CREATE INDEX IF NOT EXISTS ix_supplier_orders_external    ON supplier_orders(external_order_id);

CREATE TABLE IF NOT EXISTS system_events (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    severity   VARCHAR(20)  NOT NULL DEFAULT 'info',
    message    TEXT,
    payload    JSONB DEFAULT '{}',
    order_id   UUID REFERENCES orders(id)                ON DELETE SET NULL,
    listing_id UUID REFERENCES marketplace_listings(id)  ON DELETE SET NULL,
    product_id UUID REFERENCES products(id)              ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_system_events_type       ON system_events(event_type);
CREATE INDEX IF NOT EXISTS ix_system_events_severity   ON system_events(severity);
CREATE INDEX IF NOT EXISTS ix_system_events_order_id   ON system_events(order_id);
CREATE INDEX IF NOT EXISTS ix_system_events_listing_id ON system_events(listing_id);
CREATE INDEX IF NOT EXISTS ix_system_events_created_at ON system_events(created_at DESC);

CREATE TABLE IF NOT EXISTS marketplace_dead_letters (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id  UUID REFERENCES marketplace_listings(id) ON DELETE SET NULL,
    product_id  UUID REFERENCES products(id)             ON DELETE SET NULL,
    platform    VARCHAR(50) NOT NULL,
    operation   VARCHAR(50) NOT NULL,
    attempts    INTEGER NOT NULL DEFAULT 0,
    last_error  TEXT,
    payload     JSONB DEFAULT '{}',
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_dead_letters_platform ON marketplace_dead_letters(platform);
CREATE INDEX IF NOT EXISTS ix_dead_letters_resolved ON marketplace_dead_letters(is_resolved);

-- Retry bookkeeping for the marketplace listing state machine.
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS sync_attempts INTEGER NOT NULL DEFAULT 0;
