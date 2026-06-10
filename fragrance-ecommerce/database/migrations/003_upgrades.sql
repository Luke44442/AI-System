-- ==============================================================================
-- Aurevia Luxury Fragrance E-Commerce Platform
-- Migration 003: Upgrades — Enrichment, Analytics, Marketing & Multi-Category
-- ==============================================================================
-- Idempotent: all DDL uses IF NOT EXISTS / DO $$ guards.
-- Assumes uuid-ossp extension is already enabled (from 001).
-- ==============================================================================

-- ==============================================================================
-- 1. SUPPLIER COST HISTORY — price change audit trail
-- ==============================================================================
CREATE TABLE IF NOT EXISTS supplier_cost_history (
    id          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id UUID        NOT NULL REFERENCES suppliers(id)  ON DELETE CASCADE,
    product_id  UUID        NOT NULL REFERENCES products(id)   ON DELETE CASCADE,
    old_cost    NUMERIC(10,2),
    new_cost    NUMERIC(10,2),
    change_pct  NUMERIC(6,2),
    changed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source      VARCHAR(100),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_supplier_cost_history_product_changed
    ON supplier_cost_history (product_id, changed_at DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_cost_history_supplier_id
    ON supplier_cost_history (supplier_id);

-- ==============================================================================
-- 2. ORDER PROFITABILITY — actual profit after all fees per order
-- ==============================================================================
CREATE TABLE IF NOT EXISTS order_profitability (
    id             UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id       UUID        NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    revenue        NUMERIC(10,2),
    supplier_cost  NUMERIC(10,2),
    shipping_cost  NUMERIC(10,2),
    platform_fee   NUMERIC(10,2),
    stripe_fee     NUMERIC(10,2),
    other_fees     NUMERIC(10,2),
    gross_profit   NUMERIC(10,2),
    net_profit     NUMERIC(10,2),
    margin_pct     NUMERIC(6,2),
    channel        VARCHAR(50),
    calculated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_profitability_channel_calculated
    ON order_profitability (channel, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_order_profitability_order_id
    ON order_profitability (order_id);

-- ==============================================================================
-- 3. KEYWORD RANKINGS — SEO keyword tracker
-- ==============================================================================
CREATE TABLE IF NOT EXISTS keyword_rankings (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword         VARCHAR(500) NOT NULL,
    target_url      VARCHAR(2048),
    product_id      UUID        REFERENCES products(id) ON DELETE SET NULL,
    brand_id        UUID        REFERENCES brands(id)   ON DELETE SET NULL,
    search_engine   VARCHAR(50)  NOT NULL DEFAULT 'google',
    rank            INTEGER,
    previous_rank   INTEGER,
    rank_change     INTEGER,
    search_volume   INTEGER,
    difficulty_score NUMERIC(4,1),
    tracked_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_keyword_rankings_keyword_engine_tracked
    ON keyword_rankings (keyword, search_engine, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_keyword_rankings_product_id
    ON keyword_rankings (product_id) WHERE product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_keyword_rankings_brand_id
    ON keyword_rankings (brand_id)   WHERE brand_id IS NOT NULL;

-- ==============================================================================
-- 4. COMPETITOR PRICES — competitor price monitoring
-- ==============================================================================
CREATE TABLE IF NOT EXISTS competitor_prices (
    id               UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id       UUID        NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    competitor_name  VARCHAR(255) NOT NULL,
    competitor_url   TEXT,
    competitor_price NUMERIC(10,2),
    our_price        NUMERIC(10,2),
    price_diff       NUMERIC(10,2),
    price_diff_pct   NUMERIC(6,2),
    we_are_cheaper   BOOLEAN,
    currency         VARCHAR(3)   NOT NULL DEFAULT 'USD',
    tracked_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_competitor_prices_product_tracked
    ON competitor_prices (product_id, tracked_at DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_prices_is_active
    ON competitor_prices (is_active);

-- ==============================================================================
-- 5. PRODUCT ENRICHMENT — AI-generated fragrance data
-- ==============================================================================
CREATE TABLE IF NOT EXISTS product_enrichment (
    id                          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id                  UUID        NOT NULL UNIQUE REFERENCES products(id) ON DELETE CASCADE,
    -- Notes (stored as JSON arrays for flexibility)
    top_notes                   JSONB       NOT NULL DEFAULT '[]',
    middle_notes                JSONB       NOT NULL DEFAULT '[]',
    base_notes                  JSONB       NOT NULL DEFAULT '[]',
    fragrance_family            VARCHAR(100),
    -- Season suitability scores (0.0 – 10.0)
    season_spring               NUMERIC(3,1),
    season_summer               NUMERIC(3,1),
    season_fall                 NUMERIC(3,1),
    season_winter               NUMERIC(3,1),
    -- Occasion suitability scores (0.0 – 10.0)
    occasion_casual             NUMERIC(3,1),
    occasion_formal             NUMERIC(3,1),
    occasion_evening            NUMERIC(3,1),
    occasion_office             NUMERIC(3,1),
    occasion_outdoor            NUMERIC(3,1),
    occasion_sport              NUMERIC(3,1),
    -- Performance scores (0.0 – 10.0)
    longevity_score             NUMERIC(3,1),
    projection_score            NUMERIC(3,1),
    uniqueness_score            NUMERIC(3,1),
    value_score                 NUMERIC(3,1),
    -- Recommendations
    similar_fragrances          JSONB       NOT NULL DEFAULT '[]',
    alternative_recommendations JSONB       NOT NULL DEFAULT '[]',
    -- AI-written copy
    ai_description              TEXT,
    ai_short_description        TEXT,
    tiktok_hook                 TEXT,
    ai_generated_at             TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_enrichment_product_id
    ON product_enrichment (product_id);
CREATE INDEX IF NOT EXISTS idx_product_enrichment_fragrance_family
    ON product_enrichment (fragrance_family);

CREATE TRIGGER trg_product_enrichment_updated_at
    BEFORE UPDATE ON product_enrichment
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- 6. CONTENT ITEMS — blog posts, brand pages, guides, comparisons
-- ==============================================================================
CREATE TABLE IF NOT EXISTS content_items (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_type        VARCHAR(50) NOT NULL,
    title               VARCHAR(500),
    slug                VARCHAR(500) UNIQUE,
    excerpt             TEXT,
    body                TEXT,
    seo_title           VARCHAR(70),
    seo_description     VARCHAR(160),
    seo_keywords        JSONB       NOT NULL DEFAULT '[]',
    featured_image_url  TEXT,
    product_ids         JSONB       NOT NULL DEFAULT '[]',
    brand_ids           JSONB       NOT NULL DEFAULT '[]',
    status              VARCHAR(30) NOT NULL DEFAULT 'draft',
    published_at        TIMESTAMPTZ,
    author              VARCHAR(255) NOT NULL DEFAULT 'Aurevia Team',
    schema_markup       JSONB,
    internal_links      JSONB       NOT NULL DEFAULT '[]',
    view_count          INTEGER     NOT NULL DEFAULT 0,
    read_time_minutes   INTEGER     NOT NULL DEFAULT 5,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_items_type_status
    ON content_items (content_type, status);
CREATE INDEX IF NOT EXISTS idx_content_items_slug
    ON content_items (slug) WHERE slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_content_items_published_at
    ON content_items (published_at DESC) WHERE published_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_content_items_status
    ON content_items (status);

CREATE TRIGGER trg_content_items_updated_at
    BEFORE UPDATE ON content_items
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- 7. EMAIL SUBSCRIBERS
-- ==============================================================================
CREATE TABLE IF NOT EXISTS email_subscribers (
    id                  UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(320) NOT NULL UNIQUE,
    first_name          VARCHAR(255),
    last_name           VARCHAR(255),
    customer_id         UUID        REFERENCES customers(id) ON DELETE SET NULL,
    status              VARCHAR(30) NOT NULL DEFAULT 'subscribed'
                            CHECK (status IN ('subscribed','unsubscribed','bounced','spam')),
    source              VARCHAR(100)
                            CHECK (source IN ('homepage','checkout','popup','account') OR source IS NULL),
    tags                JSONB       NOT NULL DEFAULT '[]',
    preferences         JSONB       NOT NULL DEFAULT '{}',
    subscribed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unsubscribed_at     TIMESTAMPTZ,
    last_email_sent_at  TIMESTAMPTZ,
    open_count          INTEGER     NOT NULL DEFAULT 0,
    click_count         INTEGER     NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_subscribers_status_subscribed
    ON email_subscribers (status, subscribed_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_subscribers_customer_id
    ON email_subscribers (customer_id) WHERE customer_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_email_subscribers_email_lower
    ON email_subscribers (LOWER(email));

-- ==============================================================================
-- 8. EMAIL EVENTS — per-send event tracking
-- ==============================================================================
CREATE TABLE IF NOT EXISTS email_events (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id   UUID        NOT NULL REFERENCES email_subscribers(id) ON DELETE CASCADE,
    campaign_type   VARCHAR(50),
    subject         VARCHAR(500),
    event_type      VARCHAR(50) NOT NULL
                        CHECK (event_type IN ('sent','opened','clicked','bounced','unsubscribed')),
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_events_subscriber_type_created
    ON email_events (subscriber_id, event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_events_event_type_created
    ON email_events (event_type, created_at DESC);

-- ==============================================================================
-- 9. TIKTOK CONTENT — AI-generated TikTok scripts and performance tracking
-- ==============================================================================
CREATE TABLE IF NOT EXISTS tiktok_content (
    id                          UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id                  UUID        REFERENCES products(id) ON DELETE SET NULL,
    brand_id                    UUID        REFERENCES brands(id)   ON DELETE SET NULL,
    content_type                VARCHAR(50)
                                    CHECK (content_type IN (
                                        'product_review','duet_prompt','comparison',
                                        'hook','fragrance_story'
                                    )),
    hook                        TEXT,
    script                      TEXT,
    caption                     TEXT,
    hashtags                    JSONB       NOT NULL DEFAULT '[]',
    trending_audio_suggestions  JSONB       NOT NULL DEFAULT '[]',
    target_age_range            VARCHAR(50),
    target_gender               VARCHAR(20),
    estimated_views             INTEGER,
    status                      VARCHAR(30) NOT NULL DEFAULT 'draft',
    platform_post_id            VARCHAR(255),
    actual_views                INTEGER     NOT NULL DEFAULT 0,
    actual_likes                INTEGER     NOT NULL DEFAULT 0,
    actual_shares               INTEGER     NOT NULL DEFAULT 0,
    actual_comments             INTEGER     NOT NULL DEFAULT 0,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tiktok_content_product_status
    ON tiktok_content (product_id, status) WHERE product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tiktok_content_brand_id
    ON tiktok_content (brand_id) WHERE brand_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tiktok_content_status
    ON tiktok_content (status);
CREATE INDEX IF NOT EXISTS idx_tiktok_content_content_type
    ON tiktok_content (content_type);

CREATE TRIGGER trg_tiktok_content_updated_at
    BEFORE UPDATE ON tiktok_content
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- 10. PRICING ALERTS — pricing intelligence alerts
-- ==============================================================================
CREATE TABLE IF NOT EXISTS pricing_alerts (
    id              UUID        PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id      UUID        NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    alert_type      VARCHAR(50) NOT NULL
                        CHECK (alert_type IN (
                            'margin_low','margin_high','competitor_cheaper',
                            'cost_increase','cost_decrease'
                        )),
    message         TEXT,
    current_value   NUMERIC(10,2),
    threshold_value NUMERIC(10,2),
    is_resolved     BOOLEAN     NOT NULL DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pricing_alerts_product_resolved
    ON pricing_alerts (product_id, is_resolved);
CREATE INDEX IF NOT EXISTS idx_pricing_alerts_unresolved
    ON pricing_alerts (is_resolved, created_at DESC) WHERE NOT is_resolved;
CREATE INDEX IF NOT EXISTS idx_pricing_alerts_alert_type
    ON pricing_alerts (alert_type);

-- ==============================================================================
-- 11. PRODUCTS TABLE — multi-category columns & product_type index
-- ==============================================================================

-- Add product_type (e.g. fragrance, clothing, shoes, accessories, bags)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'product_type'
    ) THEN
        ALTER TABLE products
            ADD COLUMN product_type VARCHAR(50) NOT NULL DEFAULT 'fragrance';
    END IF;
END $$;

-- Add style_category (e.g. 'sneakers', 'hoodie', 't-shirt')
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'style_category'
    ) THEN
        ALTER TABLE products
            ADD COLUMN style_category VARCHAR(100);
    END IF;
END $$;

-- Add size_options (e.g. ['XS','S','M','L','XL'] or ['US 7','US 8'])
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'size_options'
    ) THEN
        ALTER TABLE products
            ADD COLUMN size_options JSONB NOT NULL DEFAULT '[]';
    END IF;
END $$;

-- Add color_options (e.g. ['Black','White','Navy'])
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'color_options'
    ) THEN
        ALTER TABLE products
            ADD COLUMN color_options JSONB NOT NULL DEFAULT '[]';
    END IF;
END $$;

-- Add material (e.g. '100% Cotton', 'Genuine Leather')
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'material'
    ) THEN
        ALTER TABLE products
            ADD COLUMN material VARCHAR(255);
    END IF;
END $$;

-- Add care_instructions
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'care_instructions'
    ) THEN
        ALTER TABLE products
            ADD COLUMN care_instructions TEXT;
    END IF;
END $$;

-- Index on product_type for category-level filtering
CREATE INDEX IF NOT EXISTS idx_products_product_type
    ON products (product_type);

-- Composite index: active products by type + price (mirrors existing active_category pattern)
CREATE INDEX IF NOT EXISTS idx_products_type_active_price
    ON products (product_type, is_active, website_price);
