SELECT
    CAST(transaction_datetime AS DATE)
        AS transaction_date,

    COUNT(*) AS transaction_count,

    COUNT(DISTINCT client_id)
        AS active_customer_count,

    COUNT(DISTINCT store_id)
        AS active_store_count,

    SUM(purchase_sum)
        AS total_purchase_value,

    AVG(purchase_sum)
        AS avg_basket_value,

    MEDIAN(purchase_sum)
        AS median_basket_value,

    SUM(regular_points_received)
        AS regular_points_received,

    SUM(express_points_received)
        AS express_points_received,

    SUM(regular_points_redeemed)
        AS regular_points_redeemed,

    SUM(express_points_redeemed)
        AS express_points_redeemed

FROM {{ ref('fact_transaction') }}

GROUP BY
    CAST(transaction_datetime AS DATE)