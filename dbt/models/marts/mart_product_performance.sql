WITH product_activity AS (

    SELECT
        product_id,

        COUNT(*) AS transaction_item_count,

        COUNT(DISTINCT transaction_key)
            AS transaction_count,

        COUNT(DISTINCT client_id)
            AS customer_count,

        SUM(product_quantity)
            AS units_purchased

    FROM {{ ref('fact_transaction_item') }}

    GROUP BY product_id

)

SELECT
    p.product_id,

    p.level_1,
    p.level_2,
    p.level_3,
    p.level_4,

    p.segment_id,
    p.brand_id,
    p.vendor_id,
    p.netto,

    p.is_own_trademark,
    p.is_alcohol,

    COALESCE(a.transaction_item_count, 0)
        AS transaction_item_count,

    COALESCE(a.transaction_count, 0)
        AS transaction_count,

    COALESCE(a.customer_count, 0)
        AS customer_count,

    COALESCE(a.units_purchased, 0)
        AS units_purchased

FROM {{ ref('dim_product') }} p

LEFT JOIN product_activity a
    ON p.product_id = a.product_id