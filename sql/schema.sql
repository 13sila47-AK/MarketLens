-- ============================================================================
-- MarketLens — PostgreSQL Schema
-- Phase 04: PostgreSQL + SQL
-- ============================================================================
-- Run against a real PostgreSQL instance:
--   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/schema.sql
--
-- Design notes (see research/data_model.md for full rationale):
--   - IDs are natural keys carried over from the source data (not SERIAL),
--     since this represents loading an existing company's identifiers.
--   - Revenue lives at the order_items grain; order-level revenue is always
--     a derived SUM(order_items.revenue), never stored redundantly.
--   - channel sits on orders; store_id is nullable and only populated for
--     'in-store' orders (enforced by CHECK below).
--   - competitors is a reference table (Phase 10 external research), not
--     foreign-keyed into the transactional tables.
-- ============================================================================

DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS costs CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS marketing_campaigns CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS regions CASCADE;
DROP TABLE IF EXISTS competitors CASCADE;

-- ----------------------------------------------------------------------------
-- regions
-- ----------------------------------------------------------------------------
CREATE TABLE regions (
    region_id   INTEGER PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL UNIQUE
);

-- ----------------------------------------------------------------------------
-- stores
-- ----------------------------------------------------------------------------
CREATE TABLE stores (
    store_id   INTEGER PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    region_id  INTEGER NOT NULL REFERENCES regions(region_id)
);
CREATE INDEX idx_stores_region_id ON stores(region_id);

-- ----------------------------------------------------------------------------
-- products
-- ----------------------------------------------------------------------------
CREATE TABLE products (
    product_id     INTEGER PRIMARY KEY,
    product_name   VARCHAR(150) NOT NULL,
    category       VARCHAR(50) NOT NULL CHECK (
        category IN ('Apparel', 'Home Goods', 'Electronics Accessories',
                      'Personal Care', 'Footwear')
    ),
    cost           NUMERIC(10, 2) NOT NULL CHECK (cost > 0),
    selling_price  NUMERIC(10, 2) NOT NULL CHECK (selling_price > 0),
    CHECK (cost < selling_price)
);
CREATE INDEX idx_products_category ON products(category);

-- ----------------------------------------------------------------------------
-- marketing_campaigns
-- ----------------------------------------------------------------------------
CREATE TABLE marketing_campaigns (
    campaign_id          INTEGER PRIMARY KEY,
    campaign_date        DATE NOT NULL,
    campaign_type        VARCHAR(50) NOT NULL CHECK (
        campaign_type IN ('Email', 'Social Media', 'Search Ads',
                            'Influencer', 'In-Store Promo')
    ),
    spend                NUMERIC(12, 2) NOT NULL CHECK (spend >= 0),
    customers_targeted   INTEGER NOT NULL CHECK (customers_targeted >= 0),
    customers_converted  INTEGER NOT NULL CHECK (customers_converted >= 0),
    CHECK (customers_converted <= customers_targeted)
);
CREATE INDEX idx_campaigns_date ON marketing_campaigns(campaign_date);

-- ----------------------------------------------------------------------------
-- customers
-- ----------------------------------------------------------------------------
CREATE TABLE customers (
    customer_id               INTEGER PRIMARY KEY,
    customer_name             VARCHAR(150) NOT NULL,
    signup_date               DATE NOT NULL,
    region_id                 INTEGER NOT NULL REFERENCES regions(region_id),
    acquisition_campaign_id   INTEGER REFERENCES marketing_campaigns(campaign_id)
                                  -- NULL = organic signup (no campaign credited)
);
CREATE INDEX idx_customers_region_id ON customers(region_id);
CREATE INDEX idx_customers_signup_date ON customers(signup_date);
CREATE INDEX idx_customers_acquisition_campaign ON customers(acquisition_campaign_id);

-- NOTE: customer_segment (New/Regular/Loyal/At-Risk/Churned) is deliberately
-- NOT a column here. It is derived from purchase recency/frequency in the
-- Python analytics layer (Phase 07), since it changes over time without the
-- customer's master record changing. See research/data_dictionary.md.

-- ----------------------------------------------------------------------------
-- orders
-- ----------------------------------------------------------------------------
CREATE TABLE orders (
    order_id     INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date   DATE NOT NULL,
    channel      VARCHAR(10) NOT NULL CHECK (channel IN ('online', 'in-store')),
    store_id     INTEGER REFERENCES stores(store_id),
    CHECK (
        (channel = 'online' AND store_id IS NULL) OR
        (channel = 'in-store' AND store_id IS NOT NULL)
    )
);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_store_id ON orders(store_id);

-- ----------------------------------------------------------------------------
-- order_items
-- ----------------------------------------------------------------------------
CREATE TABLE order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit_price     NUMERIC(10, 2) NOT NULL CHECK (unit_price > 0),
    discount       NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (discount >= 0),
    revenue        NUMERIC(12, 2) NOT NULL CHECK (revenue >= 0),
    CHECK (discount <= quantity * unit_price + 0.01)
);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- ----------------------------------------------------------------------------
-- returns
-- ----------------------------------------------------------------------------
CREATE TABLE returns (
    return_id       INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    return_date     DATE NOT NULL,
    return_reason   VARCHAR(50) NOT NULL CHECK (
        return_reason IN ('Wrong size', 'Defective item', 'Not as described',
                            'Changed mind', 'Better price found elsewhere',
                            'Late delivery')
    ),
    return_amount   NUMERIC(12, 2) NOT NULL CHECK (return_amount >= 0)
);
CREATE INDEX idx_returns_order_id ON returns(order_id);

-- ----------------------------------------------------------------------------
-- costs (one row per order)
-- ----------------------------------------------------------------------------
CREATE TABLE costs (
    order_id           INTEGER PRIMARY KEY REFERENCES orders(order_id) ON DELETE CASCADE,
    shipping_cost      NUMERIC(10, 2) NOT NULL CHECK (shipping_cost >= 0),
    operational_cost   NUMERIC(10, 2) NOT NULL CHECK (operational_cost >= 0)
);

-- ----------------------------------------------------------------------------
-- competitors (reference/research data — populated in Phase 10, not FK'd
-- into the transactional schema; see research/industry_analysis.md later)
-- ----------------------------------------------------------------------------
CREATE TABLE competitors (
    competitor_id       SERIAL PRIMARY KEY,
    competitor_name     VARCHAR(150) NOT NULL,
    product_focus       VARCHAR(200),
    price_positioning   VARCHAR(50),
    notable_trend       TEXT,
    source              VARCHAR(200),
    source_date         DATE
);

-- ============================================================================
-- Smoke-test query (should run without error once data is loaded — Phase 05)
-- ============================================================================
-- SELECT r.region_name AS region, SUM(oi.revenue) AS total_revenue
-- FROM order_items oi
-- JOIN orders o   ON oi.order_id = o.order_id
-- JOIN customers c ON o.customer_id = c.customer_id
-- JOIN regions r   ON c.region_id = r.region_id
-- GROUP BY r.region_name
-- ORDER BY total_revenue DESC;
--
-- Expected shape (verified against data/raw CSVs via pandas before load):
--   North   ≈ ₹289,678,800
--   East    ≈ ₹180,647,300
--   Central ≈ ₹153,314,900
--   South   ≈ ₹117,583,800
--   West    ≈ ₹115,944,200
