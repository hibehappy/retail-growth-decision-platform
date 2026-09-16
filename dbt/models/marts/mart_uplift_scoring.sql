SELECT
    f.*

FROM {{ ref('mart_customer_features') }} f

JOIN {{ ref('stg_uplift_test') }} u
    ON f.client_id = u.client_id