-- ===========================================================================
-- Migration 008: Reconcile legacy CHECK constraints with the application.
-- The original schema's CHECKs disagree with what the app actually writes,
-- so inserts/updates through the API violated constraints at runtime:
--   * products.gender             app: male/female/unisex     (was women/men)
--   * orders.payment_status       app writes 'paid'           (was missing!)
--   * orders.status               app writes 'confirmed', 'pending_payment'
--   * orders.fulfillment_status   app writes 'processing', 'shipped', ...
--   * marketplace_listings.status new sync state machine values
--   * pricing_alerts.alert_type   app writes 'low_margin'     (was margin_low)
-- Idempotent.
-- ===========================================================================

-- products.gender -----------------------------------------------------------
UPDATE products SET gender = 'female' WHERE gender = 'women';
UPDATE products SET gender = 'male'   WHERE gender = 'men';
ALTER TABLE products DROP CONSTRAINT IF EXISTS products_gender_check;
ALTER TABLE products ADD CONSTRAINT products_gender_check
  CHECK (gender IN ('male', 'female', 'unisex'));

-- orders.payment_status ('paid' is what the Stripe webhook writes) ----------
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_payment_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_payment_status_check
  CHECK (payment_status IN ('pending', 'authorized', 'captured', 'paid',
                            'failed', 'refunded', 'partially_refunded'));

-- orders.status --------------------------------------------------------------
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_status_check
  CHECK (status IN ('pending', 'pending_payment', 'confirmed', 'payment_confirmed',
                    'processing', 'sourcing', 'shipped', 'delivered',
                    'cancelled', 'refunded'));

-- orders.fulfillment_status ---------------------------------------------------
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_fulfillment_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_fulfillment_status_check
  CHECK (fulfillment_status IN ('unfulfilled', 'processing', 'partial',
                                'fulfilled', 'shipped', 'delivered'));

-- marketplace_listings.status (sync state machine) ---------------------------
ALTER TABLE marketplace_listings DROP CONSTRAINT IF EXISTS marketplace_listings_status_check;
ALTER TABLE marketplace_listings ADD CONSTRAINT marketplace_listings_status_check
  CHECK (status IN ('draft', 'pending', 'active', 'inactive', 'sold_out',
                    'deleted', 'error',
                    'created', 'uploaded', 'published', 'failed', 'retrying', 'dead'));

-- pricing_alerts.alert_type ---------------------------------------------------
UPDATE pricing_alerts SET alert_type = 'low_margin'  WHERE alert_type = 'margin_low';
UPDATE pricing_alerts SET alert_type = 'high_margin' WHERE alert_type = 'margin_high';
ALTER TABLE pricing_alerts DROP CONSTRAINT IF EXISTS pricing_alerts_alert_type_check;
ALTER TABLE pricing_alerts ADD CONSTRAINT pricing_alerts_alert_type_check
  CHECK (alert_type IN ('low_margin', 'high_margin', 'competitor_cheaper',
                        'cost_increase', 'cost_decrease'));

-- updated_at columns the ORM BaseModel expects on every mapped table --------
ALTER TABLE analytics_events      ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE collection_products   ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE competitor_prices     ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE customer_addresses    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE discount_codes        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE email_subscribers     ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE import_sessions       ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE keyword_rankings      ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE order_items           ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE order_profitability   ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE pricing_alerts        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE supplier_cost_history ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE wishlists             ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

-- created_at columns the ORM BaseModel expects -------------------------------
ALTER TABLE cart_items          ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE competitor_prices   ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE keyword_rankings    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE order_profitability ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
ALTER TABLE system_config       ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
