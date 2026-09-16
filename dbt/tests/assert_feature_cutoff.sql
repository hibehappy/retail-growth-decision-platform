SELECT
    transaction_key,
    transaction_datetime

FROM {{ ref('fact_transaction') }}

WHERE
    transaction_datetime >=
    TO_TIMESTAMP_NTZ(
        '{{ var("feature_cutoff_ts") }}'
    )