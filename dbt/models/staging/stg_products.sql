SELECT
    product_id,

    level_1,
    level_2,
    level_3,
    level_4,

    TRY_TO_NUMBER(segment_id)
        AS segment_id,

    brand_id,
    vendor_id,

    TRY_TO_DOUBLE(netto)
        AS netto,

    IFF(
        TRY_TO_NUMBER(is_own_trademark) = 1,
        TRUE,
        FALSE
    ) AS is_own_trademark,

    IFF(
        TRY_TO_NUMBER(is_alcohol) = 1,
        TRUE,
        FALSE
    ) AS is_alcohol,

    _source_file,
    _source_row_number,
    _loaded_at

FROM {{ source('x5_raw', 'products') }}