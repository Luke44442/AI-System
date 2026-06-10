-- ===========================================================================
-- Migration 004: Aurevia multi-category commerce foundation
-- Converts the fragrance-only platform into a universal multi-category catalog.
-- Idempotent: safe to run multiple times.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- 1. Category attribute schema system
--    Defines, per category, which attributes its products can carry. Drives
--    admin product forms, faceted search/filtering, and AI enrichment.
--    Actual values live in products.attributes (JSONB), keyed by `key`.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category_attributes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    key             VARCHAR(80)  NOT NULL,   -- machine key, e.g. "colorway"
    label           VARCHAR(120) NOT NULL,   -- display label, e.g. "Colorway"
    data_type       VARCHAR(20)  NOT NULL DEFAULT 'string',  -- string|number|enum|multi_enum|boolean
    options         JSONB        NOT NULL DEFAULT '[]',       -- choices for enum/multi_enum
    unit            VARCHAR(20),             -- e.g. "ml", "mm"
    is_filterable   BOOLEAN NOT NULL DEFAULT TRUE,
    is_searchable   BOOLEAN NOT NULL DEFAULT FALSE,
    is_required     BOOLEAN NOT NULL DEFAULT FALSE,
    is_variant_axis BOOLEAN NOT NULL DEFAULT FALSE,  -- generates variants (e.g. size)
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (category_id, key)
);
CREATE INDEX IF NOT EXISTS ix_category_attributes_category ON category_attributes(category_id);

-- ---------------------------------------------------------------------------
-- 2. Category metadata for multi-category routing & enrichment
-- ---------------------------------------------------------------------------
ALTER TABLE categories ADD COLUMN IF NOT EXISTS attribute_schema_type VARCHAR(50);  -- fragrance|sneakers|clothing|bags|accessories|watches|jewelry
ALTER TABLE categories ADD COLUMN IF NOT EXISTS icon VARCHAR(80);
ALTER TABLE categories ADD COLUMN IF NOT EXISTS is_featured BOOLEAN NOT NULL DEFAULT FALSE;

-- ---------------------------------------------------------------------------
-- 3. Seed the 8 top-level categories
-- ---------------------------------------------------------------------------
INSERT INTO categories (id, name, slug, description, attribute_schema_type, icon, sort_order, is_active, is_featured, product_count)
VALUES
  (gen_random_uuid(), 'Fragrances',        'fragrances',        'Designer and niche fragrances from the world''s finest houses.', 'fragrance',   'droplet',   1, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Sneakers',          'sneakers',          'Premium sneakers and rare silhouettes.',                        'sneakers',    'footprints',2, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Streetwear',        'streetwear',        'Hyped streetwear hoodies, tees, and essentials.',               'clothing',    'shirt',     3, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Designer Clothing', 'designer-clothing', 'Luxury designer apparel and ready-to-wear.',                    'clothing',    'shirt',     4, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Bags',              'bags',              'Luxury handbags, totes, and leather goods.',                    'bags',        'bag',       5, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Accessories',       'accessories',       'Sunglasses, belts, wallets, and finishing touches.',            'accessories', 'glasses',   6, TRUE, FALSE, 0),
  (gen_random_uuid(), 'Watches',           'watches',           'Timepieces and luxury watches.',                                'watches',     'watch',     7, TRUE, TRUE, 0),
  (gen_random_uuid(), 'Jewelry',           'jewelry',           'Fine and statement jewelry.',                                   'jewelry',     'gem',       8, TRUE, FALSE, 0)
ON CONFLICT (slug) DO UPDATE
  SET attribute_schema_type = EXCLUDED.attribute_schema_type,
      icon = EXCLUDED.icon,
      sort_order = EXCLUDED.sort_order,
      is_featured = EXCLUDED.is_featured;

-- ---------------------------------------------------------------------------
-- 4. Seed category attribute definitions
--    Helper inserts reference categories by slug.
-- ---------------------------------------------------------------------------

-- Fragrances ---------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('concentration',    'Concentration',    'enum',   '["Eau de Parfum","Eau de Toilette","Parfum","Extrait de Parfum","Cologne","Elixir","Eau Fraiche"]', NULL,  TRUE,  TRUE,  FALSE, 1),
  ('fragrance_family', 'Fragrance Family', 'enum',   '["Oriental","Woody","Floral","Fresh","Citrus","Aromatic","Chypre","Fougere","Gourmand","Leather"]', NULL, TRUE,  TRUE,  FALSE, 2),
  ('volume_ml',        'Volume',           'number', '[]', 'ml', TRUE,  FALSE, TRUE,  3),
  ('gender',           'Gender',           'enum',   '["Men","Women","Unisex"]', NULL, TRUE,  FALSE, FALSE, 4),
  ('longevity',        'Longevity',        'number', '[]', '/10', TRUE,  FALSE, FALSE, 5),
  ('projection',       'Projection',       'number', '[]', '/10', TRUE,  FALSE, FALSE, 6)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'fragrances'
ON CONFLICT (category_id, key) DO NOTHING;

-- Sneakers -----------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('size',         'US Size',      'enum',   '["6","6.5","7","7.5","8","8.5","9","9.5","10","10.5","11","11.5","12","13"]', NULL, TRUE, FALSE, TRUE,  1),
  ('colorway',     'Colorway',     'string', '[]', NULL, TRUE,  TRUE,  FALSE, 2),
  ('silhouette',   'Silhouette',   'string', '[]', NULL, TRUE,  TRUE,  FALSE, 3),
  ('release_year', 'Release Year', 'number', '[]', NULL, TRUE,  FALSE, FALSE, 4),
  ('material',     'Material',     'string', '[]', NULL, FALSE, TRUE,  FALSE, 5)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'sneakers'
ON CONFLICT (category_id, key) DO NOTHING;

-- Streetwear & Designer Clothing -------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('size',         'Size',         'enum',   '["XS","S","M","L","XL","XXL"]', NULL, TRUE, FALSE, TRUE,  1),
  ('fit',          'Fit',          'enum',   '["Slim","Regular","Relaxed","Oversized"]', NULL, TRUE, FALSE, FALSE, 2),
  ('garment_type', 'Type',         'enum',   '["Hoodie","T-Shirt","Sweatshirt","Sweatpants","Jacket","Jeans","Shorts","Pants","Tracksuit","Hat"]', NULL, TRUE, TRUE, FALSE, 3),
  ('season',       'Season',       'enum',   '["Spring","Summer","Fall","Winter","All-Season"]', NULL, TRUE, FALSE, FALSE, 4),
  ('material',     'Material',     'string', '[]', NULL, FALSE, TRUE,  FALSE, 5),
  ('color',        'Color',        'string', '[]', NULL, TRUE,  TRUE,  FALSE, 6)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug IN ('streetwear', 'designer-clothing')
ON CONFLICT (category_id, key) DO NOTHING;

-- Bags ---------------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('bag_type',   'Bag Type',   'enum',   '["Tote","Crossbody","Shoulder","Backpack","Clutch","Duffle","Top Handle"]', NULL, TRUE, TRUE, FALSE, 1),
  ('material',   'Material',   'enum',   '["Leather","Canvas","Suede","Nylon","Monogram Canvas"]', NULL, TRUE, TRUE, FALSE, 2),
  ('color',      'Color',      'string', '[]', NULL, TRUE,  TRUE,  FALSE, 3),
  ('dimensions', 'Dimensions', 'string', '[]', NULL, FALSE, FALSE, FALSE, 4),
  ('capacity',   'Capacity',   'string', '[]', NULL, FALSE, FALSE, FALSE, 5)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'bags'
ON CONFLICT (category_id, key) DO NOTHING;

-- Accessories --------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('accessory_type', 'Type',     'enum',   '["Sunglasses","Wallet","Belt","Hat","Scarf","Gloves","Cardholder"]', NULL, TRUE, TRUE, FALSE, 1),
  ('material',       'Material', 'string', '[]', NULL, FALSE, TRUE,  FALSE, 2),
  ('color',          'Color',    'string', '[]', NULL, TRUE,  TRUE,  FALSE, 3)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'accessories'
ON CONFLICT (category_id, key) DO NOTHING;

-- Watches ------------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('movement',         'Movement',         'enum',   '["Automatic","Quartz","Mechanical","Solar"]', NULL, TRUE, TRUE, FALSE, 1),
  ('case_size_mm',     'Case Size',        'number', '[]', 'mm', TRUE, FALSE, FALSE, 2),
  ('material',         'Case Material',    'enum',   '["Stainless Steel","Gold","Rose Gold","Titanium","Ceramic"]', NULL, TRUE, TRUE, FALSE, 3),
  ('color',            'Dial Color',       'string', '[]', NULL, TRUE,  TRUE,  FALSE, 4),
  ('water_resistance', 'Water Resistance', 'string', '[]', NULL, FALSE, FALSE, FALSE, 5)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'watches'
ON CONFLICT (category_id, key) DO NOTHING;

-- Jewelry ------------------------------------------------------------------
INSERT INTO category_attributes (category_id, key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
SELECT c.id, v.key, v.label, v.data_type, v.options::jsonb, v.unit, v.is_filterable, v.is_searchable, v.is_variant_axis, v.sort_order
FROM categories c CROSS JOIN (VALUES
  ('jewelry_type', 'Type',     'enum',   '["Necklace","Ring","Bracelet","Earrings","Chain","Pendant"]', NULL, TRUE, TRUE, FALSE, 1),
  ('material',     'Material', 'enum',   '["Gold","White Gold","Rose Gold","Silver","Platinum","Stainless Steel"]', NULL, TRUE, TRUE, FALSE, 2),
  ('gemstone',     'Gemstone', 'string', '[]', NULL, TRUE,  TRUE,  FALSE, 3),
  ('color',        'Color',    'string', '[]', NULL, TRUE,  TRUE,  FALSE, 4)
) AS v(key, label, data_type, options, unit, is_filterable, is_searchable, is_variant_axis, sort_order)
WHERE c.slug = 'jewelry'
ON CONFLICT (category_id, key) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 5. Performance: index the JSONB attributes column for faceted filtering
--    and add a full-text search vector for the universal search engine.
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS ix_products_attributes_gin ON products USING GIN (attributes);
CREATE INDEX IF NOT EXISTS ix_products_tags_gin       ON products USING GIN (tags);

-- Full-text search column (name + brand-agnostic searchable text)
ALTER TABLE products ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE OR REPLACE FUNCTION products_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'C') ||
    setweight(to_tsvector('simple', coalesce(array_to_string(NEW.tags, ' '), '')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_products_search_vector ON products;
CREATE TRIGGER trg_products_search_vector
  BEFORE INSERT OR UPDATE OF name, description, tags ON products
  FOR EACH ROW EXECUTE FUNCTION products_search_vector_update();

CREATE INDEX IF NOT EXISTS ix_products_search_vector ON products USING GIN (search_vector);

-- Backfill existing rows
UPDATE products SET search_vector =
    setweight(to_tsvector('simple', coalesce(name, '')), 'A') ||
    setweight(to_tsvector('simple', coalesce(description, '')), 'C') ||
    setweight(to_tsvector('simple', coalesce(array_to_string(tags, ' '), '')), 'B')
WHERE search_vector IS NULL;

-- updated_at trigger for category_attributes (reuses convention from migration 003)
DROP TRIGGER IF EXISTS trg_category_attributes_updated ON category_attributes;
CREATE TRIGGER trg_category_attributes_updated
  BEFORE UPDATE ON category_attributes
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
