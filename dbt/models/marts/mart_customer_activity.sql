WITH customer_activity AS (

    SELECT
        client_id,

        COUNT(*) AS transaction_count,

        MIN(transaction_datetime)
            AS first_transaction_datetime,

        MAX(transaction_datetime)
            AS last_transaction_datetime,

        COUNT(DISTINCT store_id)
            AS distinct_store_count,

        SUM(purchase_sum)
            AS total_purchase_value,

        AVG(purchase_sum)
            AS avg_basket_value,

        MEDIAN(purchase_sum)
            AS median_basket_value,

        SUM(regular_points_received)
            AS total_regular_points_received,

        SUM(express_points_received)
            AS total_express_points_received,

        SUM(regular_points_redeemed)
            AS total_regular_points_redeemed,

        SUM(express_points_redeemed)
            AS total_express_points_redeemed,

        COUNT_IF(
            regular_points_redeemed > 0
            OR express_points_redeemed > 0
        ) AS redemption_transaction_count

    FROM {{ ref('fact_transaction') }}

    GROUP BY client_id

)

SELECT
    client_id,

    transaction_count,

    first_transaction_datetime,
    last_transaction_datetime,

    distinct_store_count,

    total_purchase_value,
    avg_basket_value,
    median_basket_value,

    total_regular_points_received,
    total_express_points_received,

    total_regular_points_redeemed,
    total_express_points_redeemed,

    redemption_transaction_count,

    ROUND(
        100.0 * redemption_transaction_count
        / NULLIF(transaction_count, 0),
        2
    ) AS redemption_transaction_pct

FROM customer_activity