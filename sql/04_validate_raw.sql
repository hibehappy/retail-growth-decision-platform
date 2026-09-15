-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- RAW warehouse validation
--
-- Purpose:
-- Validate dataset grain and modeling assumptions that were
-- intentionally deferred until the full dataset was available
-- in Snowflake.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;

-- ------------------------------------------------------------
-- 1. Purchase grain
-- Expected grain:
-- one row per transaction-product pair
-- ------------------------------------------------------------

SELECT COUNT(*) AS duplicate_transaction_product_pairs
FROM (
    SELECT
        transaction_id,
        product_id
    FROM PURCHASES
    GROUP BY
        transaction_id,
        product_id
    HAVING COUNT(*) > 1
);

-- ------------------------------------------------------------
-- 2. Validate transaction-level fields
--
-- A field belongs in fact_transaction only if its value is
-- stable across every item row belonging to the transaction.
-- ------------------------------------------------------------

WITH transaction_checks AS (
    SELECT
        transaction_id,

        COUNT(DISTINCT client_id) AS client_values,
        COUNT(DISTINCT transaction_datetime) AS datetime_values,
        COUNT(DISTINCT store_id) AS store_values,
        COUNT(DISTINCT purchase_sum) AS purchase_sum_values,

        COUNT(DISTINCT regular_points_received) AS regular_received_values,
        COUNT(DISTINCT express_points_received) AS express_received_values,
        COUNT(DISTINCT regular_points_spent) AS regular_spent_values,
        COUNT(DISTINCT express_points_spent) AS express_spent_values

    FROM PURCHASES
    GROUP BY transaction_id
)

SELECT
    COUNT(*) AS total_transactions,

    COUNT_IF(client_values > 1) AS inconsistent_client,
    COUNT_IF(datetime_values > 1) AS inconsistent_datetime,
    COUNT_IF(store_values > 1) AS inconsistent_store,
    COUNT_IF(purchase_sum_values > 1) AS inconsistent_purchase_sum,

    COUNT_IF(regular_received_values > 1)
        AS inconsistent_regular_points_received,

    COUNT_IF(express_received_values > 1)
        AS inconsistent_express_points_received,

    COUNT_IF(regular_spent_values > 1)
        AS inconsistent_regular_points_spent,

    COUNT_IF(express_spent_values > 1)
        AS inconsistent_express_points_spent

FROM transaction_checks;

-- ------------------------------------------------------------
-- 3. Item-level field behavior
--
-- If these fields vary within transactions, they cannot safely
-- live at transaction grain.
-- ------------------------------------------------------------

WITH transaction_item_checks AS (
    SELECT
        transaction_id,
        COUNT(DISTINCT trn_sum_from_iss) AS iss_values,
        COUNT(DISTINCT trn_sum_from_red) AS red_values
    FROM PURCHASES
    GROUP BY transaction_id
)

SELECT
    COUNT(*) AS total_transactions,

    COUNT_IF(iss_values > 1) AS transactions_with_multiple_iss_values,
    COUNT_IF(red_values > 1) AS transactions_with_multiple_red_values

FROM transaction_item_checks;

-- ------------------------------------------------------------
-- 4. Investigate reused / inconsistent transaction IDs
-- ------------------------------------------------------------

WITH inconsistent_transactions AS (
    SELECT
        transaction_id
    FROM PURCHASES
    GROUP BY transaction_id
    HAVING
        COUNT(DISTINCT client_id) > 1
        OR COUNT(DISTINCT transaction_datetime) > 1
        OR COUNT(DISTINCT store_id) > 1
        OR COUNT(DISTINCT purchase_sum) > 1
)

SELECT DISTINCT
    p.transaction_id,
    p.client_id,
    p.transaction_datetime,
    p.store_id,
    p.purchase_sum,
    p.regular_points_received,
    p.express_points_received,
    p.regular_points_spent,
    p.express_points_spent

FROM PURCHASES p

JOIN inconsistent_transactions i
    ON p.transaction_id = i.transaction_id

ORDER BY
    p.transaction_id,
    p.client_id,
    p.transaction_datetime;

-- ------------------------------------------------------------
-- 5. Test transaction_id + client_id as transaction grain
-- ------------------------------------------------------------

WITH candidate_transactions AS (
    SELECT
        transaction_id,
        client_id,

        COUNT(DISTINCT transaction_datetime) AS datetime_values,
        COUNT(DISTINCT store_id) AS store_values,
        COUNT(DISTINCT purchase_sum) AS purchase_sum_values,

        COUNT(DISTINCT regular_points_received)
            AS regular_received_values,

        COUNT(DISTINCT express_points_received)
            AS express_received_values,

        COUNT(DISTINCT regular_points_spent)
            AS regular_spent_values,

        COUNT(DISTINCT express_points_spent)
            AS express_spent_values

    FROM PURCHASES

    GROUP BY
        transaction_id,
        client_id
)

SELECT
    COUNT(*) AS candidate_transactions,

    COUNT_IF(datetime_values > 1)
        AS inconsistent_datetime,

    COUNT_IF(store_values > 1)
        AS inconsistent_store,

    COUNT_IF(purchase_sum_values > 1)
        AS inconsistent_purchase_sum,

    COUNT_IF(regular_received_values > 1)
        AS inconsistent_regular_points_received,

    COUNT_IF(express_received_values > 1)
        AS inconsistent_express_points_received,

    COUNT_IF(regular_spent_values > 1)
        AS inconsistent_regular_points_spent,

    COUNT_IF(express_spent_values > 1)
        AS inconsistent_express_points_spent

FROM candidate_transactions;

-- ------------------------------------------------------------
-- 6. Test candidate item grain
-- ------------------------------------------------------------

SELECT COUNT(*) AS duplicate_transaction_client_product_rows
FROM (
    SELECT
        transaction_id,
        client_id,
        product_id

    FROM PURCHASES

    GROUP BY
        transaction_id,
        client_id,
        product_id

    HAVING COUNT(*) > 1
);

-- ============================================================
-- Validation conclusions
-- ============================================================

-- 1. transaction_id is not globally unique:
--    28 transaction IDs are reused across distinct customers.
--
-- 2. (transaction_id, client_id) is the validated transaction grain:
--    all tested transaction-level fields are consistent within
--    this composite key.
--
-- 3. (transaction_id, client_id, product_id) is the validated
--    transaction-item grain:
--    duplicate count = 0.
--
-- 4. trn_sum_from_iss and trn_sum_from_red vary within transactions
--    and therefore remain item-level attributes.
--
-- Warehouse implication:
-- fact_transaction      -> (transaction_id, client_id)
-- fact_transaction_item -> (transaction_id, client_id, product_id)