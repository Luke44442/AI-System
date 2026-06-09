-- ==============================================================================
-- Scentara — Indexes & Materialized Views
-- Migration 002: Performance Indexes
-- ==============================================================================

-- PRODUCTS
CREATE INDEX idx_products_sku              ON products (sku);
CREATE INDEX idx_products_slug             ON products (slug);
CREATE INDEX idx_products_brand_id         ON products (brand_id);
CREATE INDEX idx_products_category_id      ON products (category_id);
CREATE INDEX idx_products_supplier_id      ON products (supplier_id);
CREATE INDEX idx_products_gender           ON products (gender);
CREATE INDEX idx_products_is_active        ON products (is_active);
CREATE INDEX idx_products_is_featured      ON products (is_featured);
CREATE INDEX idx_products_is_bestseller    ON products (is_bestseller);
CREATE INDEX idx_products_is_new_arrival   ON products (is_new_arrival);
CREATE INDEX idx_products_inventory_status ON products (inventory_status);
CREATE INDEX idx_products_fragrance_family ON products (fragrance_family);
CREATE INDEX idx_products_website_price    ON products (website_price);
CREATE INDEX idx_products_created_at       ON products (created_at DESC);
CREATE INDEX idx_products_order_count      ON products (order_count DESC);
CREATE INDEX idx_products_rating_avg       ON products (rating_avg DESC NULLS LAST);
CREATE INDEX idx_products_search_vector    ON products USING GIN (search_vector);
CREATE INDEX idx_products_name_trgm        ON products USING GIN (name gin_trgm_ops);
CREATE INDEX idx_products_tags             ON products USING GIN (tags);
CREATE INDEX idx_products_top_notes        ON products USING GIN (top_notes);
CREATE INDEX idx_products_supplier_sku     ON products (supplier_id, supplier_sku);
CREATE INDEX idx_products_active_category  ON products (category_id, is_active, website_price);
CREATE INDEX idx_products_active_featured  ON products (is_active, is_featured, created_at DESC);
CREATE INDEX idx_products_etsy_status      ON products (etsy_status);
CREATE INDEX idx_products_ebay_status      ON products (ebay_status);

-- PRODUCT VARIANTS
CREATE INDEX idx_product_variants_product_id ON product_variants (product_id);
CREATE INDEX idx_product_variants_sku        ON product_variants (sku);

-- COLLECTIONS
CREATE INDEX idx_collections_slug        ON collections (slug);
CREATE INDEX idx_collections_is_active   ON collections (is_active);
CREATE INDEX idx_collections_is_featured ON collections (is_featured);
CREATE INDEX idx_collection_products_collection_id ON collection_products (collection_id, sort_order);
CREATE INDEX idx_collection_products_product_id    ON collection_products (product_id);

-- CUSTOMERS
CREATE UNIQUE INDEX idx_customers_email    ON customers (LOWER(email));
CREATE INDEX idx_customers_is_active       ON customers (is_active);
CREATE INDEX idx_customers_stripe_id       ON customers (stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX idx_customers_created_at      ON customers (created_at DESC);

-- ORDERS
CREATE UNIQUE INDEX idx_orders_order_number ON orders (order_number);
CREATE INDEX idx_orders_customer_id         ON orders (customer_id);
CREATE INDEX idx_orders_channel             ON orders (channel);
CREATE INDEX idx_orders_status              ON orders (status);
CREATE INDEX idx_orders_payment_status      ON orders (payment_status);
CREATE INDEX idx_orders_created_at          ON orders (created_at DESC);
CREATE INDEX idx_orders_status_created      ON orders (status, created_at DESC);
CREATE INDEX idx_orders_tracking_number     ON orders (tracking_number) WHERE tracking_number IS NOT NULL;
CREATE INDEX idx_orders_payment_intent_id   ON orders (payment_intent_id) WHERE payment_intent_id IS NOT NULL;
CREATE INDEX idx_orders_external_order_id   ON orders (external_order_id) WHERE external_order_id IS NOT NULL;

-- ORDER ITEMS
CREATE INDEX idx_order_items_order_id   ON order_items (order_id);
CREATE INDEX idx_order_items_product_id ON order_items (product_id);
CREATE INDEX idx_order_items_created_at ON order_items (created_at DESC);

-- MARKETPLACE LISTINGS
CREATE INDEX idx_marketplace_listings_product_id  ON marketplace_listings (product_id);
CREATE INDEX idx_marketplace_listings_marketplace ON marketplace_listings (marketplace);
CREATE INDEX idx_marketplace_listings_status      ON marketplace_listings (status);
CREATE INDEX idx_marketplace_listings_next_sync   ON marketplace_listings (next_sync_at) WHERE next_sync_at IS NOT NULL;

-- ANALYTICS
CREATE INDEX idx_analytics_events_session_id ON analytics_events (session_id);
CREATE INDEX idx_analytics_events_event_type ON analytics_events (event_type);
CREATE INDEX idx_analytics_events_product_id ON analytics_events (product_id) WHERE product_id IS NOT NULL;
CREATE INDEX idx_analytics_events_created_at ON analytics_events (created_at DESC);
CREATE INDEX idx_analytics_events_type_date  ON analytics_events (event_type, created_at DESC);

-- REVIEWS
CREATE INDEX idx_reviews_product_id   ON reviews (product_id);
CREATE INDEX idx_reviews_is_published ON reviews (is_published);
CREATE INDEX idx_reviews_published_product ON reviews (product_id, is_published, helpful_count DESC);

-- WISHLISTS & CARTS
CREATE INDEX idx_wishlists_customer_id ON wishlists (customer_id);
CREATE INDEX idx_carts_customer_id     ON carts (customer_id) WHERE customer_id IS NOT NULL;
CREATE UNIQUE INDEX idx_carts_session_token ON carts (session_token);
CREATE INDEX idx_carts_expires_at      ON carts (expires_at);
CREATE INDEX idx_cart_items_cart_id    ON cart_items (cart_id);
CREATE INDEX idx_cart_items_product_id ON cart_items (product_id);

-- MARKETING
CREATE INDEX idx_marketing_content_product_id ON marketing_content (product_id) WHERE product_id IS NOT NULL;
CREATE INDEX idx_marketing_content_platform   ON marketing_content (platform);
CREATE INDEX idx_marketing_content_status     ON marketing_content (status);

-- ==============================================================================
-- MATERIALIZED VIEWS
-- ==============================================================================
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT
    DATE_TRUNC('day', o.created_at AT TIME ZONE 'UTC')::DATE  AS revenue_date,
    o.channel,
    o.currency,
    COUNT(*)                                                    AS order_count,
    SUM(o.total) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) AS net_revenue,
    SUM(o.profit_amount) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) AS total_profit,
    CASE
        WHEN SUM(o.total) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) > 0
        THEN ROUND((SUM(o.profit_amount) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) /
                    SUM(o.total) FILTER (WHERE o.status NOT IN ('cancelled','refunded'))) * 100, 2)
        ELSE 0
    END AS profit_margin_pct,
    CASE
        WHEN COUNT(*) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) > 0
        THEN ROUND(SUM(o.total) FILTER (WHERE o.status NOT IN ('cancelled','refunded')) /
                   COUNT(*) FILTER (WHERE o.status NOT IN ('cancelled','refunded')), 2)
        ELSE 0
    END AS avg_order_value,
    NOW() AS last_refreshed_at
FROM orders o
GROUP BY DATE_TRUNC('day', o.created_at AT TIME ZONE 'UTC')::DATE, o.channel, o.currency
WITH DATA;

CREATE UNIQUE INDEX idx_daily_revenue_date_channel ON daily_revenue (revenue_date, channel, currency);
CREATE INDEX idx_daily_revenue_date ON daily_revenue (revenue_date DESC);

CREATE MATERIALIZED VIEW product_performance AS
WITH order_stats AS (
    SELECT oi.product_id,
           COUNT(DISTINCT oi.order_id) AS order_count,
           SUM(oi.quantity)            AS units_sold,
           SUM(oi.total)               AS gross_revenue,
           SUM(oi.total - oi.supplier_cost * oi.quantity) AS gross_profit
    FROM order_items oi
    JOIN orders o ON o.id = oi.order_id
    WHERE o.status NOT IN ('cancelled','refunded')
    GROUP BY oi.product_id
),
review_stats AS (
    SELECT product_id,
           COUNT(*) FILTER (WHERE is_published) AS review_count,
           ROUND(AVG(rating), 2)               AS avg_rating
    FROM reviews
    GROUP BY product_id
)
SELECT
    p.id AS product_id, p.sku, p.name, p.brand_id, p.category_id,
    p.website_price, p.total_cost, p.website_margin_pct,
    p.inventory_status, p.is_active, p.is_featured,
    COALESCE(os.order_count, 0)    AS order_count,
    COALESCE(os.units_sold, 0)     AS units_sold,
    COALESCE(os.gross_revenue, 0)  AS gross_revenue,
    COALESCE(os.gross_profit, 0)   AS gross_profit,
    COALESCE(rs.review_count, 0)   AS review_count,
    rs.avg_rating,
    NOW() AS last_refreshed_at
FROM products p
LEFT JOIN order_stats os ON os.product_id = p.id
LEFT JOIN review_stats rs ON rs.product_id = p.id
WITH DATA;

CREATE UNIQUE INDEX idx_product_performance_id ON product_performance (product_id);
CREATE INDEX idx_product_performance_revenue   ON product_performance (gross_revenue DESC);
CREATE INDEX idx_product_performance_orders    ON product_performance (order_count DESC);

-- Refresh functions (called by Celery beat)
CREATE OR REPLACE FUNCTION refresh_daily_revenue() RETURNS VOID LANGUAGE SQL AS $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;
$$;

CREATE OR REPLACE FUNCTION refresh_product_performance() RETURNS VOID LANGUAGE SQL AS $$
  REFRESH MATERIALIZED VIEW CONCURRENTLY product_performance;
$$;
