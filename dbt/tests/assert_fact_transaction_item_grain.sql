SELECT
    transaction_key,
    product_id,
    COUNT(*) AS row_count

FROM {{ ref('fact_transaction_item') }}

GROUP BY
    transaction_key,
    product_id

HAVING COUNT(*) > 1