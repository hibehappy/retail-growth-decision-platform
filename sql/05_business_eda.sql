-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- Business SQL analysis
--
-- Purpose:
-- Understand customer, transaction, product, loyalty, store,
-- and temporal behavior before designing dbt marts.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;


-- ============================================================
-- Analytical base grains
-- ============================================================

-- One row per validated transaction:
-- (transaction_id, client_id)

CREATE OR REPLACE TEMP VIEW TMP_TRANSACTION AS

SELECT
    transaction_id,
    client_id,

    MAX(TRY_TO_TIMESTAMP_NTZ(transaction_datetime))
        AS transaction_datetime,

    MAX(store_id)
        AS store_id,

    MAX(TRY_TO_DOUBLE(purchase_sum))
        AS purchase_sum,

    MAX(TRY_TO_DOUBLE(regular_points_received))
        AS regular_points_received,

    MAX(TRY_TO_DOUBLE(express_points_received))
        AS express_points_received,

    MAX(TRY_TO_DOUBLE(regular_points_spent))
        AS regular_points_spent,

    MAX(TRY_TO_DOUBLE(express_points_spent))
        AS express_points_spent

FROM PURCHASES

GROUP BY
    transaction_id,
    client_id;


-- One row per validated transaction-item:
-- (transaction_id, client_id, product_id)

CREATE OR REPLACE TEMP VIEW TMP_TRANSACTION_ITEM AS

SELECT
    transaction_id,
    client_id,
    product_id,

    TRY_TO_DOUBLE(product_quantity)
        AS product_quantity,

    TRY_TO_DOUBLE(trn_sum_from_iss)
        AS trn_sum_from_iss,

    TRY_TO_DOUBLE(trn_sum_from_red)
        AS trn_sum_from_red

FROM PURCHASES;

-- ============================================================
-- 1. Core business KPIs
-- ============================================================

WITH item_summary AS (
    SELECT
        transaction_id,
        client_id,

        COUNT(*) AS product_lines,
        COUNT(DISTINCT product_id) AS unique_products,
        SUM(product_quantity) AS units

    FROM TMP_TRANSACTION_ITEM

    GROUP BY
        transaction_id,
        client_id
)

SELECT
    COUNT(*) AS transactions,

    COUNT(DISTINCT t.client_id)
        AS purchasing_customers,

    ROUND(SUM(t.purchase_sum), 2)
        AS total_purchase_value,

    ROUND(AVG(t.purchase_sum), 2)
        AS avg_basket_value,

    ROUND(AVG(i.product_lines), 2)
        AS avg_product_lines_per_transaction,

    ROUND(AVG(i.unique_products), 2)
        AS avg_unique_products_per_transaction,

    ROUND(AVG(i.units), 2)
        AS avg_units_per_transaction

FROM TMP_TRANSACTION t

JOIN item_summary i
    ON t.transaction_id = i.transaction_id
    AND t.client_id = i.client_id;

-- ============================================================
-- 2. Customer purchase behavior
-- ============================================================

WITH customer_summary AS (
    SELECT
        client_id,

        COUNT(*) AS transactions,
        SUM(purchase_sum) AS total_spend,
        AVG(purchase_sum) AS avg_basket_value

    FROM TMP_TRANSACTION

    GROUP BY client_id
)

SELECT
    COUNT(*) AS purchasing_customers,

    ROUND(AVG(transactions), 2)
        AS avg_transactions_per_customer,

    MEDIAN(transactions)
        AS median_transactions_per_customer,

    ROUND(
        100.0 * COUNT_IF(transactions >= 2) / COUNT(*),
        2
    ) AS repeat_customer_pct,

    ROUND(AVG(total_spend), 2)
        AS avg_customer_spend,

    ROUND(MEDIAN(total_spend), 2)
        AS median_customer_spend,

    ROUND(AVG(avg_basket_value), 2)
        AS avg_customer_basket_value

FROM customer_summary;

-- ============================================================
-- 3. Daily activity
-- ============================================================

SELECT
    DATE(transaction_datetime)
        AS transaction_date,

    COUNT(*)
        AS transactions,

    COUNT(DISTINCT client_id)
        AS active_customers,

    ROUND(SUM(purchase_sum), 2)
        AS purchase_value,

    ROUND(AVG(purchase_sum), 2)
        AS avg_basket_value

FROM TMP_TRANSACTION

GROUP BY transaction_date

ORDER BY transaction_date;

-- ============================================================
-- 4. Category activity
--
-- purchase_sum is intentionally excluded because it lives at
-- transaction grain and cannot safely be assigned to products.
-- ============================================================

SELECT
    p.level_1,

    COUNT(DISTINCT i.transaction_id, i.client_id)
        AS transactions_with_category,

    COUNT(DISTINCT i.client_id)
        AS customers,

    COUNT(DISTINCT i.product_id)
        AS products,

    ROUND(SUM(i.product_quantity), 2)
        AS units

FROM TMP_TRANSACTION_ITEM i

JOIN PRODUCTS p
    ON i.product_id = p.product_id

GROUP BY p.level_1

ORDER BY transactions_with_category DESC;

-- ============================================================
-- 5. Loyalty behavior
--
-- Points earned are positive.
-- Points redeemed/spent are stored as negative values.
-- ============================================================

SELECT
    COUNT(*) AS transactions,

    ROUND(
        100.0 *
        COUNT_IF(
            regular_points_received > 0
            OR express_points_received > 0
        )
        / COUNT(*),
        2
    ) AS pct_transactions_earning_points,

    ROUND(
        100.0 *
        COUNT_IF(
            regular_points_spent < 0
            OR express_points_spent < 0
        )
        / COUNT(*),
        2
    ) AS pct_transactions_redeeming_points,

    ROUND(AVG(regular_points_received), 2)
        AS avg_regular_points_received,

    ROUND(AVG(express_points_received), 2)
        AS avg_express_points_received,

    ROUND(
        AVG(
            CASE
                WHEN regular_points_spent < 0
                THEN ABS(regular_points_spent)
            END
        ),
        2
    ) AS avg_regular_points_redeemed_when_used,

    ROUND(
        AVG(
            CASE
                WHEN express_points_spent < 0
                THEN ABS(express_points_spent)
            END
        ),
        2
    ) AS avg_express_points_redeemed_when_used

FROM TMP_TRANSACTION;

-- ============================================================
-- 6. Store activity
-- ============================================================

SELECT
    store_id,

    COUNT(*) AS transactions,

    COUNT(DISTINCT client_id)
        AS customers,

    ROUND(SUM(purchase_sum), 2)
        AS purchase_value,

    ROUND(AVG(purchase_sum), 2)
        AS avg_basket_value

FROM TMP_TRANSACTION

GROUP BY store_id

ORDER BY transactions DESC;