SELECT
    client_id,
    treatment_flg,
    target

FROM {{ ref('stg_uplift_train') }}