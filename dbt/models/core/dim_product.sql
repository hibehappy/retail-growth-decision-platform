SELECT
    product_id,

    level_1,
    level_2,
    level_3,
    level_4,

    segment_id,
    brand_id,
    vendor_id,
    netto,

    is_own_trademark,
    is_alcohol

FROM {{ ref('stg_products') }}