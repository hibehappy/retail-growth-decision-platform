SELECT
    transaction_key,
    transaction_id,
    client_id,
    product_id,

    product_quantity,

    trn_sum_from_iss,
    trn_sum_from_red

FROM {{ ref('stg_purchases') }}