-- ============================================================================
-- MarketLens — Data Quality & Validation Queries
-- Phase 06: Data Quality & Validation
-- ============================================================================
-- Run against a live PostgreSQL instance loaded via Phase 04's
-- load_to_postgres.py:
--   psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f sql/data_quality.sql
--
-- This is the SQL-native counterpart to python/validation/data_quality.py.
-- Both check the same four categories (missing values, duplicates, invalid
-- values, cross-source integrity); the Python script is what actually runs
-- in this build environment (no live Postgres here), this file is the
-- production-path equivalent for whoever loads the DB for real.
--
-- Every query below should return ZERO rows on clean data. A non-empty
-- result identifies exactly which records fail the rule.
-- ============================================================================


-- ============================================================================
-- 1. MISSING VALUES
-- ============================================================================

-- 1.1 customers missing required fields
SELECT 'customers' AS table_name, customer_id, 'missing required field' AS issue
FROM customers
WHERE customer_name IS NULL OR signup_date IS NULL OR region_id IS NULL;

-- 1.2 orders missing required fields
SELECT 'orders' AS table_name, order_id, 'missing required field' AS issue
FROM orders
WHERE customer_id IS NULL OR order_date IS NULL OR channel IS NULL;

-- 1.3 in-store orders missing store_id (should be impossible — CHECK constraint)
SELECT 'orders' AS table_name, order_id, 'in-store order missing store_id' AS issue
FROM orders
WHERE channel = 'in-store' AND store_id IS NULL;

-- 1.4 order_items missing required fields
SELECT 'order_items' AS table_name, order_item_id, 'missing required field' AS issue
FROM order_items
WHERE order_id IS NULL OR product_id IS NULL OR quantity IS NULL
   OR unit_price IS NULL OR revenue IS NULL;


-- ============================================================================
-- 2. DUPLICATES
-- ============================================================================

-- 2.1 duplicate customer_id (should be impossible — PRIMARY KEY)
SELECT 'customers' AS table_name, customer_id, COUNT(*) AS n
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

-- 2.2 duplicate order_id
SELECT 'orders' AS table_name, order_id, COUNT(*) AS n
FROM orders
GROUP BY order_id
HAVING COUNT(*) > 1;

-- 2.3 duplicate order_item_id
SELECT 'order_items' AS table_name, order_item_id, COUNT(*) AS n
FROM order_items
GROUP BY order_item_id
HAVING COUNT(*) > 1;

-- 2.4 duplicate product_id
SELECT 'products' AS table_name, product_id, COUNT(*) AS n
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1;

-- 2.5 customers that look like duplicate people (same name + signup_date —
-- not a hard PK violation, but worth flagging for manual review)
SELECT 'customers' AS table_name, customer_name, signup_date, COUNT(*) AS n
FROM customers
GROUP BY customer_name, signup_date
HAVING COUNT(*) > 1;


-- ============================================================================
-- 3. INVALID VALUES
-- ============================================================================

-- 3.1 negative or zero revenue
SELECT 'order_items' AS table_name, order_item_id, revenue
FROM order_items
WHERE revenue < 0;

-- 3.2 non-positive quantity
SELECT 'order_items' AS table_name, order_item_id, quantity
FROM order_items
WHERE quantity <= 0;

-- 3.3 discount exceeds order value
SELECT 'order_items' AS table_name, order_item_id, discount, quantity * unit_price AS order_value
FROM order_items
WHERE discount > quantity * unit_price + 0.01;

-- 3.4 revenue doesn't reconcile to qty*price - discount
SELECT 'order_items' AS table_name, order_item_id,
       revenue, (quantity * unit_price - discount) AS expected_revenue
FROM order_items
WHERE ABS(revenue - (quantity * unit_price - discount)) > 0.01;

-- 3.5 invalid / out-of-range order_date
SELECT 'orders' AS table_name, order_id, order_date
FROM orders
WHERE order_date < DATE '2020-01-01' OR order_date > DATE '2026-12-31';

-- 3.6 negative return_amount
SELECT 'returns' AS table_name, return_id, return_amount
FROM returns
WHERE return_amount < 0;

-- 3.7 campaign converted more customers than targeted (should be impossible — CHECK)
SELECT 'marketing_campaigns' AS table_name, campaign_id,
       customers_targeted, customers_converted
FROM marketing_campaigns
WHERE customers_converted > customers_targeted;

-- 3.8 product cost >= selling_price (impossible margin, should be impossible — CHECK)
SELECT 'products' AS table_name, product_id, cost, selling_price
FROM products
WHERE cost >= selling_price;


-- ============================================================================
-- 4. CROSS-SOURCE / REFERENTIAL INTEGRITY
-- ============================================================================
-- These are enforced by FOREIGN KEY constraints in schema.sql, so on a
-- properly loaded DB they will always return zero rows. Still worth running
-- explicitly as a top-level data-quality gate, independent of relying on the
-- schema having been applied correctly.

-- 4.1 orders referencing a non-existent customer
SELECT 'orders' AS table_name, o.order_id, o.customer_id
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

-- 4.2 order_items referencing a non-existent order
SELECT 'order_items' AS table_name, oi.order_item_id, oi.order_id
FROM order_items oi
LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 4.3 order_items referencing a non-existent product
SELECT 'order_items' AS table_name, oi.order_item_id, oi.product_id
FROM order_items oi
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE p.product_id IS NULL;

-- 4.4 returns referencing a non-existent order
SELECT 'returns' AS table_name, r.return_id, r.order_id
FROM returns r
LEFT JOIN orders o ON r.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 4.5 costs referencing a non-existent order
SELECT 'costs' AS table_name, co.order_id
FROM costs co
LEFT JOIN orders o ON co.order_id = o.order_id
WHERE o.order_id IS NULL;

-- 4.6 orders missing a costs row (should be exactly 1:1)
SELECT 'orders' AS table_name, o.order_id
FROM orders o
LEFT JOIN costs co ON o.order_id = co.order_id
WHERE co.order_id IS NULL;

-- 4.7 orders with zero order_items (an order should always have >= 1 line item)
SELECT 'orders' AS table_name, o.order_id
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.order_item_id IS NULL;


-- ============================================================================
-- 5. SUMMARY REPORT
-- ============================================================================
-- One-shot rollup: rows processed per table, and a total count of records
-- that fail any hard-integrity rule above. Mirrors the report format that
-- python/validation/data_quality.py produces from the CSVs.

WITH row_counts AS (
    SELECT 'regions' AS table_name, COUNT(*) AS n FROM regions
    UNION ALL SELECT 'stores', COUNT(*) FROM stores
    UNION ALL SELECT 'products', COUNT(*) FROM products
    UNION ALL SELECT 'marketing_campaigns', COUNT(*) FROM marketing_campaigns
    UNION ALL SELECT 'customers', COUNT(*) FROM customers
    UNION ALL SELECT 'orders', COUNT(*) FROM orders
    UNION ALL SELECT 'order_items', COUNT(*) FROM order_items
    UNION ALL SELECT 'returns', COUNT(*) FROM returns
    UNION ALL SELECT 'costs', COUNT(*) FROM costs
),
invalid_revenue AS (
    SELECT COUNT(*) AS n FROM order_items WHERE revenue < 0
),
orphan_orders AS (
    SELECT COUNT(*) AS n FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL
),
bad_discounts AS (
    SELECT COUNT(*) AS n FROM order_items
    WHERE discount > quantity * unit_price + 0.01
)
SELECT
    (SELECT SUM(n) FROM row_counts)      AS total_rows_processed,
    (SELECT n FROM invalid_revenue)      AS negative_revenue_rows,
    (SELECT n FROM orphan_orders)        AS orphan_order_rows,
    (SELECT n FROM bad_discounts)        AS invalid_discount_rows;
