-- ===========================================================================
-- Migration 006: Reconcile marketplace_listings with the ORM + multi-marketplace
-- The original table used `marketplace` with a CHECK limiting platforms to
-- etsy/ebay/facebook and lacked the columns the app writes. This aligns the
-- table with the MarketplaceListing model and opens it to all platforms.
-- Idempotent.
-- ===========================================================================

-- Drop the restrictive platform CHECK so TikTok Shop / Pinterest / Google work.
ALTER TABLE marketplace_listings DROP CONSTRAINT IF EXISTS marketplace_listings_marketplace_check;

-- Rename marketplace -> platform (only if platform doesn't already exist).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='marketplace_listings' AND column_name='marketplace')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_name='marketplace_listings' AND column_name='platform') THEN
    ALTER TABLE marketplace_listings RENAME COLUMN marketplace TO platform;
  END IF;
END $$;

-- Ensure the columns the ORM/sync service writes exist.
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS platform    VARCHAR(50);
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS quantity    INTEGER NOT NULL DEFAULT 0;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS sync_error  TEXT;

-- Replace the old unique (product_id, marketplace) with (product_id, platform).
ALTER TABLE marketplace_listings DROP CONSTRAINT IF EXISTS marketplace_listings_product_id_marketplace_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_listing_product_platform ON marketplace_listings(product_id, platform);
CREATE INDEX IF NOT EXISTS ix_marketplace_listings_platform ON marketplace_listings(platform);
CREATE INDEX IF NOT EXISTS ix_marketplace_listings_status   ON marketplace_listings(status);
