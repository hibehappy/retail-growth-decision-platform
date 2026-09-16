SELECT

    {{ generate_transaction_key(
        'transaction_id',
        'client_id'
    ) }} AS transaction_key,

    transaction_id,
    client_id,
    product_id,

    TRY_TO_TIMESTAMP_NTZ(transaction_datetime)
        AS transaction_datetime,

    store_id,

    TRY_TO_DOUBLE(purchase_sum)
        AS purchase_sum,

    TRY_TO_DOUBLE(regular_points_received)
        AS regular_points_received,

    TRY_TO_DOUBLE(express_points_received)
        AS express_points_received,

    TRY_TO_DOUBLE(regular_points_spent)
        AS regular_points_spent,

    TRY_TO_DOUBLE(express_points_spent)
        AS express_points_spent,

    TRY_TO_DOUBLE(product_quantity)
        AS product_quantity,

    TRY_TO_DOUBLE(trn_sum_from_iss)
        AS trn_sum_from_iss,

    TRY_TO_DOUBLE(trn_sum_from_red)
        AS trn_sum_from_red,

    _source_file,
    _source_row_number,
    _loaded_at

FROM {{ source('x5_raw', 'purchases') }}