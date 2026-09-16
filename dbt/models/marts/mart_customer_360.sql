SELECT
    c.client_id,

    c.first_issue_date,
    c.first_redeem_date,

    c.age_raw,
    c.age,
    c.age_invalid_flag,

    c.gender,

    c.has_redeemed,
    c.redeem_before_issue_flag,

    COALESCE(a.transaction_count, 0)
        AS transaction_count,

    a.first_transaction_datetime,
    a.last_transaction_datetime,

    COALESCE(a.distinct_store_count, 0)
        AS distinct_store_count,

    COALESCE(a.total_purchase_value, 0)
        AS total_purchase_value,

    a.avg_basket_value,
    a.median_basket_value,

    COALESCE(a.total_regular_points_received, 0)
        AS total_regular_points_received,

    COALESCE(a.total_express_points_received, 0)
        AS total_express_points_received,

    COALESCE(a.total_regular_points_redeemed, 0)
        AS total_regular_points_redeemed,

    COALESCE(a.total_express_points_redeemed, 0)
        AS total_express_points_redeemed,

    COALESCE(a.redemption_transaction_count, 0)
        AS redemption_transaction_count,

    COALESCE(a.redemption_transaction_pct, 0)
        AS redemption_transaction_pct

FROM {{ ref('dim_customer') }} c

LEFT JOIN {{ ref('mart_customer_activity') }} a
    ON c.client_id = a.client_id