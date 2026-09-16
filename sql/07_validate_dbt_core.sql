-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- dbt core model validation
--
-- Purpose:
-- Confirm that dbt core models preserve the validated
-- business grains and expected source populations.
-- ============================================================

USE ROLE DBT_DEV_ROLE;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;


-- ------------------------------------------------------------
-- Core model row counts
-- ------------------------------------------------------------

SELECT
    'DIM_CUSTOMER' AS model,
    COUNT(*) AS row_count
FROM RETAIL_GROWTH.DEV_CORE.DIM_CUSTOMER

UNION ALL

SELECT
    'DIM_PRODUCT',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_CORE.DIM_PRODUCT

UNION ALL

SELECT
    'FACT_TRANSACTION',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_CORE.FACT_TRANSACTION

UNION ALL

SELECT
    'FACT_TRANSACTION_ITEM',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_CORE.FACT_TRANSACTION_ITEM

UNION ALL

SELECT
    'FACT_TREATMENT_OUTCOME',
    COUNT(*)
FROM RETAIL_GROWTH.DEV_CORE.FACT_TREATMENT_OUTCOME;