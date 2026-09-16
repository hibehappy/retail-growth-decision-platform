-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- dbt analytical mart validation
--
-- Purpose:
-- Confirm that analytical marts preserve their intended
-- business grains and expected populations.
-- ============================================================

USE ROLE DBT_DEV_ROLE;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;


-- ------------------------------------------------------------
-- Mart row counts
-- ------------------------------------------------------------

SELECT
    'MART_CUSTOMER_ACTIVITY' AS model,
    COUNT(*) AS row_count
FROM RETAIL_GROWTH.DEV_MARTS.MART_CUSTOMER_ACTIVITY

UNION ALL

SELECT
    'MART_PURCHASE_DAILY',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_MARTS.MART_PURCHASE_DAILY

UNION ALL

SELECT
    'MART_PRODUCT_PERFORMANCE',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_MARTS.MART_PRODUCT_PERFORMANCE

UNION ALL

SELECT
    'MART_CUSTOMER_360',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_MARTS.MART_CUSTOMER_360;

-- ------------------------------------------------------------
-- Customer mart reconciliation
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS customers,

    SUM(transaction_count)
        AS reconstructed_transactions,

    ROUND(SUM(total_purchase_value), 2)
        AS reconstructed_purchase_value

FROM RETAIL_GROWTH.DEV_MARTS.MART_CUSTOMER_ACTIVITY;