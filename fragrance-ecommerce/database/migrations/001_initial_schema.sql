-- ==============================================================================
-- Aurevia Luxury Fragrance E-Commerce Platform
-- Migration 001: Initial Schema
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Updated-at trigger
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Order number sequence
CREATE SEQUENCE IF NOT EXISTS order_number_seq START WITH 10001 INCREMENT BY 1;

CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.order_number IS NULL OR NEW.order_number = '' THEN
    NEW.order_number := 'SCN-' || LPAD(NEXTVAL('order_number_seq')::TEXT, 6, '0');
  END IF;
  RETURN NEW;
END;
$$;

-- ==============================================================================
-- BRANDS
-- ==============================================================================
CREATE TABLE brands (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    slug        VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    logo_url    TEXT,
    website_url TEXT,
    is_luxury   BOOLEAN NOT NULL DEFAULT TRUE,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_brands_updated_at BEFORE UPDATE ON brands FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- CATEGORIES
-- ==============================================================================
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id       UUID REFERENCES categories(id) ON DELETE SET NULL,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) NOT NULL UNIQUE,
    description     TEXT,
    seo_title       VARCHAR(70),
    seo_description VARCHAR(160),
    image_url       TEXT,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    product_count   INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_categories_updated_at BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

INSERT INTO categories (name, slug, description, seo_title, seo_description, sort_order) VALUES
    ('Women''s Perfume',   'womens-perfume',   'Luxury fragrances for women',               'Women''s Perfume | Aurevia',        'Shop premium women''s perfumes at Aurevia.',           1),
    ('Men''s Cologne',     'mens-cologne',     'Premium colognes and eau de toilette',       'Men''s Cologne | Aurevia',          'Discover exceptional men''s colognes at Aurevia.',     2),
    ('Unisex Fragrance',   'unisex-fragrance', 'Gender-neutral luxury fragrances',           'Unisex Fragrances | Aurevia',       'Explore unisex and gender-neutral fragrances.',          3),
    ('Eau de Parfum',      'eau-de-parfum',    'Long-lasting EDP concentrations',            'Eau de Parfum | Aurevia',           'Browse rich Eau de Parfum fragrances.',                  4),
    ('Eau de Toilette',    'eau-de-toilette',  'Fresh and light EDT fragrances',             'Eau de Toilette | Aurevia',         'Shop fresh Eau de Toilette fragrances.',                 5),
    ('Parfum & Extrait',   'parfum-extrait',   'Ultra-concentrated parfum',                  'Parfum & Extrait | Aurevia',        'Discover the most opulent parfum extraits.',             6),
    ('Floral',             'floral',           'Romantic floral fragrances',                 'Floral Fragrances | Aurevia',       'Shop beautiful floral fragrances.',                      7),
    ('Oriental & Woody',   'oriental-woody',   'Rich oriental and woody families',           'Oriental & Woody | Aurevia',        'Explore warm oriental and woody fragrances.',            8),
    ('Fresh & Aquatic',    'fresh-aquatic',    'Light, fresh and aquatic fragrances',        'Fresh & Aquatic | Aurevia',         'Shop crisp fresh fragrances for everyday wear.',         9),
    ('Gift Sets',          'gift-sets',        'Luxury fragrance gift sets',                 'Fragrance Gift Sets | Aurevia',     'Find the perfect luxury fragrance gift.',                10);

-- ==============================================================================
-- SUPPLIERS
-- ==============================================================================
CREATE TABLE suppliers (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                  VARCHAR(255) NOT NULL UNIQUE,
    slug                  VARCHAR(255) NOT NULL UNIQUE,
    type                  VARCHAR(50) NOT NULL DEFAULT 'other',
    base_url              TEXT,
    credentials           JSONB NOT NULL DEFAULT '{}',
    default_shipping_cost DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    avg_processing_days   INTEGER NOT NULL DEFAULT 3,
    avg_shipping_days     INTEGER NOT NULL DEFAULT 14,
    reliability_score     DECIMAL(3,2) NOT NULL DEFAULT 4.00,
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    config                JSONB NOT NULL DEFAULT '{}',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_suppliers_updated_at BEFORE UPDATE ON suppliers FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

INSERT INTO suppliers (name, slug, type, base_url, default_shipping_cost, avg_processing_days, avg_shipping_days, reliability_score) VALUES
    ('OrientDig',  'orientdig', 'orientdig', 'https://www.orientdig.com', 4.99, 2, 12, 4.20),
    ('CNShopper',  'cnshopper', 'cnshopper', 'https://www.cnshopper.com', 3.99, 3, 16, 3.90);

-- ==============================================================================
-- PRODUCTS
-- ==============================================================================
CREATE TABLE products (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku                   VARCHAR(100) NOT NULL UNIQUE,
    brand_id              UUID REFERENCES brands(id) ON DELETE SET NULL,
    category_id           UUID REFERENCES categories(id) ON DELETE SET NULL,
    supplier_id           UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    name                  VARCHAR(500) NOT NULL,
    slug                  VARCHAR(500) NOT NULL UNIQUE,
    description           TEXT,
    short_description     TEXT,
    fragrance_family      VARCHAR(100),
    concentration         VARCHAR(50),
    gender                VARCHAR(20) NOT NULL DEFAULT 'unisex' CHECK (gender IN ('women', 'men', 'unisex')),
    volume_ml             INTEGER,
    launch_year           SMALLINT,
    top_notes             TEXT[],
    middle_notes          TEXT[],
    base_notes            TEXT[],
    nose                  VARCHAR(255),
    supplier_cost         DECIMAL(10,2),
    shipping_cost         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_cost            DECIMAL(10,2) GENERATED ALWAYS AS (COALESCE(supplier_cost, 0) + shipping_cost) STORED,
    website_price         DECIMAL(10,2),
    marketplace_price     DECIMAL(10,2),
    compare_at_price      DECIMAL(10,2),
    website_margin_pct    DECIMAL(5,2) GENERATED ALWAYS AS (
                              CASE WHEN website_price > 0 AND COALESCE(supplier_cost, 0) + shipping_cost > 0
                                   THEN ROUND(((website_price - (COALESCE(supplier_cost, 0) + shipping_cost)) / website_price) * 100, 2)
                                   ELSE NULL END) STORED,
    marketplace_margin_pct DECIMAL(5,2) GENERATED ALWAYS AS (
                              CASE WHEN marketplace_price > 0 AND COALESCE(supplier_cost, 0) + shipping_cost > 0
                                   THEN ROUND(((marketplace_price - (COALESCE(supplier_cost, 0) + shipping_cost)) / marketplace_price) * 100, 2)
                                   ELSE NULL END) STORED,
    inventory_status      VARCHAR(20) NOT NULL DEFAULT 'in_stock' CHECK (inventory_status IN ('in_stock', 'out_of_stock', 'low_stock', 'discontinued', 'pre_order')),
    inventory_quantity    INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold   INTEGER NOT NULL DEFAULT 5,
    supplier_sku          VARCHAR(255),
    supplier_url          TEXT,
    supplier_price        DECIMAL(10,2),
    supplier_data         JSONB DEFAULT '{}',
    seo_title             VARCHAR(70),
    seo_description       VARCHAR(160),
    seo_keywords          TEXT[],
    structured_data       JSONB DEFAULT '{}',
    images                JSONB NOT NULL DEFAULT '[]',
    is_active             BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured           BOOLEAN NOT NULL DEFAULT FALSE,
    is_bestseller         BOOLEAN NOT NULL DEFAULT FALSE,
    is_new_arrival        BOOLEAN NOT NULL DEFAULT TRUE,
    etsy_listing_id       VARCHAR(100),
    etsy_status           VARCHAR(30) NOT NULL DEFAULT 'not_listed',
    ebay_listing_id       VARCHAR(100),
    ebay_status           VARCHAR(30) NOT NULL DEFAULT 'not_listed',
    facebook_listing_id   VARCHAR(100),
    facebook_status       VARCHAR(30) NOT NULL DEFAULT 'not_listed',
    tags                  TEXT[] DEFAULT '{}',
    attributes            JSONB DEFAULT '{}',
    search_vector         TSVECTOR,
    ai_generated_listing  BOOLEAN NOT NULL DEFAULT FALSE,
    view_count            INTEGER NOT NULL DEFAULT 0,
    order_count           INTEGER NOT NULL DEFAULT 0,
    revenue_total         DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    rating_avg            DECIMAL(3,2),
    review_count          INTEGER NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE OR REPLACE FUNCTION products_search_vector_update() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.search_vector :=
    SETWEIGHT(TO_TSVECTOR('english', COALESCE(NEW.name, '')), 'A') ||
    SETWEIGHT(TO_TSVECTOR('english', COALESCE(NEW.short_description, '')), 'B') ||
    SETWEIGHT(TO_TSVECTOR('english', COALESCE(NEW.description, '')), 'C') ||
    SETWEIGHT(TO_TSVECTOR('english', COALESCE(NEW.fragrance_family, '')), 'B') ||
    SETWEIGHT(TO_TSVECTOR('english', COALESCE(ARRAY_TO_STRING(NEW.tags, ' '), '')), 'C');
  RETURN NEW;
END; $$;
CREATE TRIGGER trg_products_search_vector BEFORE INSERT OR UPDATE ON products FOR EACH ROW EXECUTE FUNCTION products_search_vector_update();

-- ==============================================================================
-- PRODUCT VARIANTS
-- ==============================================================================
CREATE TABLE product_variants (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id          UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku                 VARCHAR(100) NOT NULL UNIQUE,
    name                VARCHAR(255) NOT NULL,
    volume_ml           INTEGER,
    supplier_cost       DECIMAL(10,2),
    website_price       DECIMAL(10,2),
    marketplace_price   DECIMAL(10,2),
    inventory_quantity  INTEGER NOT NULL DEFAULT 0,
    supplier_sku        VARCHAR(255),
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_product_variants_updated_at BEFORE UPDATE ON product_variants FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- COLLECTIONS
-- ==============================================================================
CREATE TABLE collections (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              VARCHAR(255) NOT NULL,
    slug              VARCHAR(255) NOT NULL UNIQUE,
    subtitle          VARCHAR(255),
    description       TEXT,
    seo_title         VARCHAR(70),
    seo_description   VARCHAR(160),
    image_url         TEXT,
    banner_url        TEXT,
    sort_order        INTEGER NOT NULL DEFAULT 0,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured       BOOLEAN NOT NULL DEFAULT FALSE,
    is_automated      BOOLEAN NOT NULL DEFAULT FALSE,
    automation_rules  JSONB DEFAULT '{}',
    product_count     INTEGER NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_collections_updated_at BEFORE UPDATE ON collections FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TABLE collection_products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id   UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (collection_id, product_id)
);

INSERT INTO collections (name, slug, subtitle, seo_title, seo_description, sort_order, is_featured, is_automated, automation_rules) VALUES
    ('New Arrivals',     'new-arrivals',     'Fresh off the bottle',     'New Fragrances | Aurevia',          'Shop the latest luxury fragrances just added.',                 1, TRUE,  TRUE,  '{"rules":[{"field":"is_new_arrival","operator":"eq","value":true}]}'),
    ('Best Sellers',     'best-sellers',     'Loved by thousands',       'Best Selling Fragrances | Aurevia', 'Shop our most popular luxury fragrances.',                      2, TRUE,  TRUE,  '{"rules":[{"field":"is_bestseller","operator":"eq","value":true}]}'),
    ('Summer Scents',    'summer-scents',    'Light, fresh & vibrant',   'Summer Fragrances | Aurevia',       'Fresh and vibrant summer fragrances.',                          3, TRUE,  FALSE, '{}'),
    ('Floral Collection','floral-collection','Blooms in a bottle',        'Floral Perfumes | Aurevia',         'Romantic floral perfumes featuring rose and jasmine.',          4, FALSE, TRUE,  '{"rules":[{"field":"fragrance_family","operator":"contains","value":"floral"}]}'),
    ('Oriental & Woody', 'oriental-woody',   'Deep, rich & mysterious',  'Oriental & Woody | Aurevia',        'Warm oriental fragrances with oud, amber, and sandalwood.',     5, FALSE, TRUE,  '{"rules":[{"field":"fragrance_family","operator":"in","value":["oriental","woody"]}]}'),
    ('Under $50',        'under-50',         'Luxury within reach',      'Fragrances Under $50 | Aurevia',    'Premium fragrances priced under $50.',                          6, TRUE,  TRUE,  '{"rules":[{"field":"website_price","operator":"lte","value":50}]}');

-- ==============================================================================
-- CUSTOMERS
-- ==============================================================================
CREATE TABLE customers (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email                   VARCHAR(255) NOT NULL UNIQUE,
    first_name              VARCHAR(100),
    last_name               VARCHAR(100),
    phone                   VARCHAR(30),
    password_hash           TEXT,
    auth_provider           VARCHAR(30) NOT NULL DEFAULT 'email',
    avatar_url              TEXT,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified             BOOLEAN NOT NULL DEFAULT FALSE,
    is_admin                BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at       TIMESTAMPTZ,
    marketing_consent       BOOLEAN NOT NULL DEFAULT FALSE,
    order_count             INTEGER NOT NULL DEFAULT 0,
    total_spent             DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    avg_order_value         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    last_order_at           TIMESTAMPTZ,
    preferred_scent_families TEXT[] DEFAULT '{}',
    stripe_customer_id      VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TABLE customer_addresses (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id   UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    address_type  VARCHAR(20) NOT NULL DEFAULT 'shipping',
    is_default    BOOLEAN NOT NULL DEFAULT FALSE,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    company       VARCHAR(255),
    address1      VARCHAR(255) NOT NULL,
    address2      VARCHAR(255),
    city          VARCHAR(100) NOT NULL,
    state         VARCHAR(100),
    postal_code   VARCHAR(20) NOT NULL,
    country       CHAR(2) NOT NULL DEFAULT 'US',
    phone         VARCHAR(30),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- ORDERS
-- ==============================================================================
CREATE TABLE orders (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number          VARCHAR(50) UNIQUE,
    customer_id           UUID REFERENCES customers(id) ON DELETE SET NULL,
    guest_email           VARCHAR(255),
    customer_name         VARCHAR(255),
    channel               VARCHAR(50) NOT NULL DEFAULT 'website' CHECK (channel IN ('website','etsy','ebay','facebook','manual')),
    external_order_id     VARCHAR(255),
    status                VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','payment_confirmed','processing','sourcing','shipped','delivered','cancelled','refunded')),
    payment_status        VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending','authorized','captured','failed','refunded')),
    fulfillment_status    VARCHAR(50) NOT NULL DEFAULT 'unfulfilled' CHECK (fulfillment_status IN ('unfulfilled','partial','fulfilled')),
    subtotal              DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    shipping_amount       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    tax_amount            DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total                 DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency              CHAR(3) NOT NULL DEFAULT 'USD',
    supplier_cost_total   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    profit_amount         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    shipping_address      JSONB,
    billing_address       JSONB,
    payment_method        VARCHAR(50),
    payment_provider      VARCHAR(50),
    payment_intent_id     VARCHAR(255),
    supplier_id           UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    supplier_order_id     VARCHAR(255),
    supplier_order_url    TEXT,
    supplier_order_data   JSONB DEFAULT '{}',
    shipping_method       VARCHAR(100),
    tracking_number       VARCHAR(255),
    tracking_url          TEXT,
    carrier               VARCHAR(100),
    payment_confirmed_at  TIMESTAMPTZ,
    shipped_at            TIMESTAMPTZ,
    delivered_at          TIMESTAMPTZ,
    cancelled_at          TIMESTAMPTZ,
    discount_code         VARCHAR(100),
    customer_note         TEXT,
    internal_note         TEXT,
    ip_address            INET,
    user_agent            TEXT,
    tags                  TEXT[] DEFAULT '{}',
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER trg_orders_number BEFORE INSERT ON orders FOR EACH ROW EXECUTE FUNCTION generate_order_number();

CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID REFERENCES products(id) ON DELETE SET NULL,
    variant_id          UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    sku                 VARCHAR(100) NOT NULL,
    name                VARCHAR(500) NOT NULL,
    image_url           TEXT,
    quantity            INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price          DECIMAL(10,2) NOT NULL,
    supplier_cost       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total               DECIMAL(10,2) NOT NULL,
    supplier_sku        VARCHAR(255),
    fulfillment_status  VARCHAR(50) NOT NULL DEFAULT 'unfulfilled',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- MARKETPLACE LISTINGS
-- ==============================================================================
CREATE TABLE marketplace_listings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    marketplace     VARCHAR(50) NOT NULL CHECK (marketplace IN ('etsy','ebay','facebook')),
    listing_id      VARCHAR(255),
    listing_url     TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','pending','active','inactive','sold_out','deleted','error')),
    title           VARCHAR(500),
    description     TEXT,
    price           DECIMAL(10,2),
    compare_at_price DECIMAL(10,2),
    platform_data   JSONB DEFAULT '{}',
    sync_errors     JSONB NOT NULL DEFAULT '[]',
    last_synced_at  TIMESTAMPTZ,
    next_sync_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (product_id, marketplace)
);
CREATE TRIGGER trg_marketplace_listings_updated_at BEFORE UPDATE ON marketplace_listings FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- PRICING RULES
-- ==============================================================================
CREATE TABLE pricing_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    marketplace         VARCHAR(50),
    base_markup_pct     DECIMAL(6,2) NOT NULL DEFAULT 50.00,
    marketplace_fee_pct DECIMAL(6,2) NOT NULL DEFAULT 0.00,
    payment_fee_pct     DECIMAL(6,2) NOT NULL DEFAULT 3.00,
    shipping_buffer     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    min_margin_pct      DECIMAL(6,2) NOT NULL DEFAULT 15.00,
    target_margin_pct   DECIMAL(6,2) NOT NULL DEFAULT 30.00,
    price_rounding      VARCHAR(20) NOT NULL DEFAULT 'round_99',
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_pricing_rules_updated_at BEFORE UPDATE ON pricing_rules FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

INSERT INTO pricing_rules (name, description, marketplace, base_markup_pct, marketplace_fee_pct, payment_fee_pct, shipping_buffer, min_margin_pct, target_margin_pct, price_rounding) VALUES
    ('Website Default',            'Default pricing for the Aurevia storefront.',         NULL,       70.00, 0.00,  2.90, 0.00, 20.00, 35.00, 'round_99'),
    ('Etsy Pricing',               'Etsy: 6.5% transaction + $0.20 listing fee.',          'etsy',     80.00, 6.50,  3.00, 0.50, 18.00, 32.00, 'round_99'),
    ('eBay Pricing',               'eBay: ~12.9% final value fee.',                        'ebay',     90.00, 12.90, 2.90, 1.00, 18.00, 30.00, 'round_00'),
    ('Facebook Marketplace',       'Facebook: 5% selling fee.',                            'facebook', 75.00, 5.00,  2.90, 0.00, 18.00, 32.00, 'round_99');

-- ==============================================================================
-- IMPORT SESSIONS
-- ==============================================================================
CREATE TABLE import_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id     UUID REFERENCES suppliers(id) ON DELETE SET NULL,
    filename        VARCHAR(500) NOT NULL,
    file_type       VARCHAR(10) NOT NULL DEFAULT 'csv' CHECK (file_type IN ('csv','xlsx')),
    file_size       BIGINT,
    storage_key     TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','completed','failed')),
    total_rows      INTEGER,
    processed_rows  INTEGER NOT NULL DEFAULT 0,
    imported_count  INTEGER NOT NULL DEFAULT 0,
    updated_count   INTEGER NOT NULL DEFAULT 0,
    skipped_count   INTEGER NOT NULL DEFAULT 0,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    error_count     INTEGER NOT NULL DEFAULT 0,
    column_mapping  JSONB DEFAULT '{}',
    errors          JSONB DEFAULT '[]',
    warnings        JSONB DEFAULT '[]',
    summary         JSONB DEFAULT '{}',
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_by      UUID REFERENCES customers(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- REVIEWS
-- ==============================================================================
CREATE TABLE reviews (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id              UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    customer_id             UUID REFERENCES customers(id) ON DELETE SET NULL,
    order_id                UUID REFERENCES orders(id) ON DELETE SET NULL,
    rating                  SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title                   VARCHAR(255),
    body                    TEXT,
    longevity_rating        SMALLINT CHECK (longevity_rating >= 1 AND longevity_rating <= 5),
    sillage_rating          SMALLINT CHECK (sillage_rating >= 1 AND sillage_rating <= 5),
    value_rating            SMALLINT CHECK (value_rating >= 1 AND value_rating <= 5),
    reviewer_name           VARCHAR(100),
    is_verified_purchase    BOOLEAN NOT NULL DEFAULT FALSE,
    is_published            BOOLEAN NOT NULL DEFAULT FALSE,
    is_featured             BOOLEAN NOT NULL DEFAULT FALSE,
    helpful_count           INTEGER NOT NULL DEFAULT 0,
    admin_reply             TEXT,
    admin_reply_at          TIMESTAMPTZ,
    images                  JSONB DEFAULT '[]',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON reviews FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- WISHLISTS & CARTS
-- ==============================================================================
CREATE TABLE wishlists (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (customer_id, product_id)
);

CREATE TABLE carts (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id   UUID REFERENCES customers(id) ON DELETE SET NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    coupon_code   VARCHAR(100),
    expires_at    TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_carts_updated_at BEFORE UPDATE ON carts FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TABLE cart_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cart_id     UUID NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
    product_id  UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id  UUID REFERENCES product_variants(id) ON DELETE CASCADE,
    quantity    INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    added_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (cart_id, product_id, variant_id)
);
CREATE TRIGGER trg_cart_items_updated_at BEFORE UPDATE ON cart_items FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- DISCOUNT CODES
-- ==============================================================================
CREATE TABLE discount_codes (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code              VARCHAR(100) NOT NULL UNIQUE,
    description       TEXT,
    type              VARCHAR(30) NOT NULL DEFAULT 'percentage' CHECK (type IN ('percentage','fixed_amount','free_shipping')),
    value             DECIMAL(10,2) NOT NULL,
    min_order_amount  DECIMAL(10,2),
    max_uses          INTEGER,
    uses_count        INTEGER NOT NULL DEFAULT 0,
    starts_at         TIMESTAMPTZ,
    expires_at        TIMESTAMPTZ,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- ANALYTICS EVENTS
-- ==============================================================================
CREATE TABLE analytics_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      VARCHAR(255),
    customer_id     UUID REFERENCES customers(id) ON DELETE SET NULL,
    event_type      VARCHAR(100) NOT NULL,
    event_category  VARCHAR(100),
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,
    collection_id   UUID REFERENCES collections(id) ON DELETE SET NULL,
    page_url        TEXT,
    referrer        TEXT,
    utm_source      VARCHAR(100),
    utm_medium      VARCHAR(100),
    utm_campaign    VARCHAR(255),
    properties      JSONB DEFAULT '{}',
    ip_address      INET,
    user_agent      TEXT,
    device_type     VARCHAR(30),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- MARKETING CONTENT
-- ==============================================================================
CREATE TABLE marketing_content (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id        UUID REFERENCES products(id) ON DELETE SET NULL,
    platform          VARCHAR(50) NOT NULL CHECK (platform IN ('tiktok','instagram','pinterest','facebook')),
    content_type      VARCHAR(100) NOT NULL,
    caption           TEXT,
    hashtags          TEXT[] DEFAULT '{}',
    image_urls        TEXT[] DEFAULT '{}',
    video_url         TEXT,
    status            VARCHAR(30) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','scheduled','published','failed')),
    scheduled_at      TIMESTAMPTZ,
    published_at      TIMESTAMPTZ,
    platform_post_id  VARCHAR(255),
    ai_generated      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TRIGGER trg_marketing_content_updated_at BEFORE UPDATE ON marketing_content FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ==============================================================================
-- SYSTEM CONFIG
-- ==============================================================================
CREATE TABLE system_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    type        VARCHAR(30) NOT NULL DEFAULT 'string',
    description TEXT,
    is_public   BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO system_config (key, value, type, description, is_public) VALUES
    ('site.name',                     '"Aurevia"',                      'string',  'Store name',                              TRUE),
    ('site.tagline',                  '"Luxury Fragrances, Delivered"',   'string',  'Store tagline',                           TRUE),
    ('site.currency',                 '"USD"',                            'string',  'Default currency',                        TRUE),
    ('shipping.free_threshold_usd',   '75.00',                            'number',  'Free shipping above this amount',          TRUE),
    ('shipping.default_cost',         '9.99',                             'number',  'Default shipping cost',                    TRUE),
    ('inventory.low_stock_threshold', '5',                                'integer', 'Global low stock threshold',               FALSE),
    ('pricing.website_markup_pct',    '65.0',                             'number',  'Default website markup %',                 FALSE),
    ('pricing.marketplace_markup_pct','55.0',                             'number',  'Default marketplace markup %',             FALSE),
    ('ai.auto_generate_listings',     'true',                             'boolean', 'Auto-generate AI listings on import',      FALSE),
    ('reviews.auto_publish',          'false',                            'boolean', 'Auto-publish reviews without moderation',  FALSE);
