SELECT
    f.*,

    y.treatment_flg,
    y.target

FROM {{ ref('mart_customer_features') }} f

JOIN {{ ref('fact_treatment_outcome') }} y
    ON f.client_id = y.client_id