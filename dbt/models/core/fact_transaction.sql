SELECT
    transaction_key,
    transaction_id,
    client_id,

    MAX(transaction_datetime)
        AS transaction_datetime,

    MAX(store_id)
        AS store_id,

    MAX(purchase_sum)
        AS purchase_sum,

    MAX(regular_points_received)
        AS regular_points_received,

    MAX(express_points_received)
        AS express_points_received,

    MAX(regular_points_spent)
        AS regular_points_spent,

    MAX(express_points_spent)
        AS express_points_spent,

    CASE
        WHEN MAX(regular_points_spent) < 0
        THEN ABS(MAX(regular_points_spent))
        ELSE 0
    END AS regular_points_redeemed,

    CASE
        WHEN MAX(express_points_spent) < 0
        THEN ABS(MAX(express_points_spent))
        ELSE 0
    END AS express_points_redeemed

FROM {{ ref('stg_purchases') }}

GROUP BY
    transaction_key,
    transaction_id,
    client_id