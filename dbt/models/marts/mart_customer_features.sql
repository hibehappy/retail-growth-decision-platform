WITH params AS (

    SELECT
        TO_TIMESTAMP_NTZ(
            '{{ var("feature_cutoff_ts") }}'
        ) AS feature_cutoff_ts

),

transaction_features AS (

    SELECT
        t.client_id,

        COUNT(*)
            AS transaction_count,

        SUM(t.purchase_sum)
            AS total_purchase_value,

        AVG(t.purchase_sum)
            AS avg_basket_value,

        MEDIAN(t.purchase_sum)
            AS median_basket_value,

        STDDEV_SAMP(t.purchase_sum)
            AS basket_value_stddev,

        MAX(t.purchase_sum)
            AS max_basket_value,

        COUNT(DISTINCT t.store_id)
            AS distinct_store_count,

        DATEDIFF(
            'day',
            MAX(t.transaction_datetime),
            p.feature_cutoff_ts
        ) AS recency_days,

        DATEDIFF(
            'day',
            MIN(t.transaction_datetime),
            MAX(t.transaction_datetime)
        ) + 1 AS active_history_days,

        COUNT_IF(
            t.transaction_datetime >=
            DATEADD('day', -30, p.feature_cutoff_ts)
        ) AS transaction_count_30d,

        SUM(
            IFF(
                t.transaction_datetime >=
                DATEADD('day', -30, p.feature_cutoff_ts),
                t.purchase_sum,
                0
            )
        ) AS purchase_value_30d,

        COUNT_IF(
            t.transaction_datetime >=
                DATEADD('day', -60, p.feature_cutoff_ts)
            AND t.transaction_datetime <
                DATEADD('day', -30, p.feature_cutoff_ts)
        ) AS transaction_count_prior_30d,

        SUM(
            IFF(
                t.transaction_datetime >=
                    DATEADD('day', -60, p.feature_cutoff_ts)
                AND t.transaction_datetime <
                    DATEADD('day', -30, p.feature_cutoff_ts),
                t.purchase_sum,
                0
            )
        ) AS purchase_value_prior_30d,

        SUM(t.regular_points_received)
            AS total_regular_points_received,

        SUM(t.express_points_received)
            AS total_express_points_received,

        SUM(t.regular_points_redeemed)
            AS total_regular_points_redeemed,

        SUM(t.express_points_redeemed)
            AS total_express_points_redeemed,

        COUNT_IF(
            t.regular_points_redeemed > 0
            OR t.express_points_redeemed > 0
        ) AS redemption_transaction_count

    FROM {{ ref('fact_transaction') }} t

    CROSS JOIN params p

    WHERE
        t.transaction_datetime < p.feature_cutoff_ts

    GROUP BY
        t.client_id,
        p.feature_cutoff_ts

),

product_features AS (

    SELECT
        i.client_id,

        COUNT(*)
            AS item_line_count,

        COUNT(DISTINCT i.product_id)
            AS distinct_product_count,

        COUNT(DISTINCT p.level_1)
            AS distinct_level1_category_count,

        SUM(i.product_quantity)
            AS total_product_units,

        ROUND(
            100.0 *
            COUNT_IF(p.is_own_trademark = TRUE)
            / NULLIF(COUNT(*), 0),
            2
        ) AS own_trademark_item_pct,

        ROUND(
            100.0 *
            COUNT_IF(p.is_alcohol = TRUE)
            / NULLIF(COUNT(*), 0),
            2
        ) AS alcohol_item_pct,

        ROUND(
            100.0 *
            COUNT_IF(p.level_1 = 'e344ab2e71')
            / NULLIF(COUNT(*), 0),
            2
        ) AS category_e344ab2e71_item_pct,

        ROUND(
            100.0 *
            COUNT_IF(p.level_1 = 'c3d3a8e8c6')
            / NULLIF(COUNT(*), 0),
            2
        ) AS category_c3d3a8e8c6_item_pct,

        ROUND(
            100.0 *
            COUNT_IF(p.level_1 = 'ec62ce61e3')
            / NULLIF(COUNT(*), 0),
            2
        ) AS category_ec62ce61e3_item_pct

    FROM {{ ref('fact_transaction_item') }} i

    JOIN {{ ref('fact_transaction') }} t
        ON i.transaction_key = t.transaction_key

    JOIN {{ ref('dim_product') }} p
        ON i.product_id = p.product_id

    CROSS JOIN params cutoff

    WHERE
        t.transaction_datetime < cutoff.feature_cutoff_ts

    GROUP BY
        i.client_id

)

SELECT
    c.client_id,

    /* --------------------------------------------------------
       Customer attributes available at feature time
       -------------------------------------------------------- */

    c.age,
    c.gender,

    DATEDIFF(
        'day',
        c.first_issue_date,
        p.feature_cutoff_ts
    ) AS customer_tenure_days,

    IFF(
        c.first_redeem_date IS NOT NULL
        AND c.first_redeem_date >= c.first_issue_date
        AND c.first_redeem_date < p.feature_cutoff_ts,
        1,
        0
    ) AS redeemed_before_cutoff_flag,

    /* --------------------------------------------------------
       RFM / transaction behavior
       -------------------------------------------------------- */

    COALESCE(t.transaction_count, 0)
        AS transaction_count,

    COALESCE(t.recency_days, 0)
        AS recency_days,

    COALESCE(t.active_history_days, 0)
        AS active_history_days,

    COALESCE(t.total_purchase_value, 0)
        AS total_purchase_value,

    COALESCE(t.avg_basket_value, 0)
        AS avg_basket_value,

    COALESCE(t.median_basket_value, 0)
        AS median_basket_value,

    COALESCE(t.basket_value_stddev, 0)
        AS basket_value_stddev,

    COALESCE(t.max_basket_value, 0)
        AS max_basket_value,

    COALESCE(t.distinct_store_count, 0)
        AS distinct_store_count,

    /* --------------------------------------------------------
       Recent behavior
       -------------------------------------------------------- */

    COALESCE(t.transaction_count_30d, 0)
        AS transaction_count_30d,

    COALESCE(t.purchase_value_30d, 0)
        AS purchase_value_30d,

    COALESCE(t.transaction_count_prior_30d, 0)
        AS transaction_count_prior_30d,

    COALESCE(t.purchase_value_prior_30d, 0)
        AS purchase_value_prior_30d,

    ROUND(
        100.0 * COALESCE(t.transaction_count_30d, 0)
        / NULLIF(t.transaction_count, 0),
        2
    ) AS transaction_30d_pct,

    ROUND(
        100.0 * COALESCE(t.purchase_value_30d, 0)
        / NULLIF(t.total_purchase_value, 0),
        2
    ) AS purchase_value_30d_pct,

    /* --------------------------------------------------------
       Loyalty behavior
       -------------------------------------------------------- */

    COALESCE(t.total_regular_points_received, 0)
        AS total_regular_points_received,

    COALESCE(t.total_express_points_received, 0)
        AS total_express_points_received,

    COALESCE(t.total_regular_points_redeemed, 0)
        AS total_regular_points_redeemed,

    COALESCE(t.total_express_points_redeemed, 0)
        AS total_express_points_redeemed,

    COALESCE(t.redemption_transaction_count, 0)
        AS redemption_transaction_count,

    ROUND(
        100.0 * COALESCE(t.redemption_transaction_count, 0)
        / NULLIF(t.transaction_count, 0),
        2
    ) AS redemption_transaction_pct,

    /* --------------------------------------------------------
       Product / category behavior
       -------------------------------------------------------- */

    COALESCE(i.item_line_count, 0)
        AS item_line_count,

    COALESCE(i.distinct_product_count, 0)
        AS distinct_product_count,

    COALESCE(i.distinct_level1_category_count, 0)
        AS distinct_level1_category_count,

    COALESCE(i.total_product_units, 0)
        AS total_product_units,

    COALESCE(i.own_trademark_item_pct, 0)
        AS own_trademark_item_pct,

    COALESCE(i.alcohol_item_pct, 0)
        AS alcohol_item_pct,

    COALESCE(i.category_e344ab2e71_item_pct, 0)
        AS category_e344ab2e71_item_pct,

    COALESCE(i.category_c3d3a8e8c6_item_pct, 0)
        AS category_c3d3a8e8c6_item_pct,

    COALESCE(i.category_ec62ce61e3_item_pct, 0)
        AS category_ec62ce61e3_item_pct

FROM {{ ref('dim_customer') }} c

CROSS JOIN params p

LEFT JOIN transaction_features t
    ON c.client_id = t.client_id

LEFT JOIN product_features i
    ON c.client_id = i.client_id