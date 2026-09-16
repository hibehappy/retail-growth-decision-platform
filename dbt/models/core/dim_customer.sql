SELECT
    client_id,

    first_issue_date,
    first_redeem_date,

    age_raw,
    age,
    age_invalid_flag,

    gender,

    has_redeemed,
    redeem_before_issue_flag

FROM {{ ref('stg_clients') }}