-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- ML feature-layer validation
--
-- Purpose:
-- Confirm feature population, train/test partition, and
-- pre-communication feature cutoff integrity.
-- ============================================================

USE ROLE DBT_DEV_ROLE;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;


-- ------------------------------------------------------------
-- Feature populations
-- ------------------------------------------------------------

SELECT
    'MART_CUSTOMER_FEATURES' AS model,
    COUNT(*) AS row_count
FROM RETAIL_GROWTH.DEV_MARTS.MART_CUSTOMER_FEATURES

UNION ALL

SELECT
    'MART_UPLIFT_TRAINING',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_MARTS.MART_UPLIFT_TRAINING

UNION ALL

SELECT
    'MART_UPLIFT_SCORING',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_MARTS.MART_UPLIFT_SCORING;


-- ------------------------------------------------------------
-- Expected feature cutoff
-- ------------------------------------------------------------

SELECT
    MAX(transaction_datetime)
        AS latest_historical_transaction,

    TO_TIMESTAMP_NTZ('2019-03-19 00:00:00')
        AS feature_cutoff,

    COUNT_IF(
        transaction_datetime >=
        TO_TIMESTAMP_NTZ('2019-03-19 00:00:00')
    ) AS transactions_at_or_after_cutoff

FROM RETAIL_GROWTH.DEV_CORE.FACT_TRANSACTION;


-- ------------------------------------------------------------
-- Train / scoring population integrity
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS overlap_count

FROM RETAIL_GROWTH.DEV_MARTS.MART_UPLIFT_TRAINING train

JOIN RETAIL_GROWTH.DEV_MARTS.MART_UPLIFT_SCORING score
    ON train.client_id = score.client_id;