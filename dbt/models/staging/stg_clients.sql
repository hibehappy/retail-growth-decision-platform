WITH source AS (

    SELECT *
    FROM {{ source('x5_raw', 'clients') }}

),

typed AS (

    SELECT
        client_id,

        TRY_TO_TIMESTAMP_NTZ(first_issue_date)
            AS first_issue_date,

        TRY_TO_TIMESTAMP_NTZ(first_redeem_date)
            AS first_redeem_date,

        age AS age_raw,

        TRY_TO_NUMBER(age)
            AS age_numeric,

        gender,

        _source_file,
        _source_row_number,
        _loaded_at

    FROM source

)

SELECT
    client_id,
    first_issue_date,
    first_redeem_date,

    age_raw,

    CASE
        WHEN age_numeric BETWEEN 0 AND 120
        THEN age_numeric
    END AS age,

    IFF(
        age_numeric IS NULL
        OR age_numeric NOT BETWEEN 0 AND 120,
        TRUE,
        FALSE
    ) AS age_invalid_flag,

    gender,

    IFF(
        first_redeem_date IS NOT NULL,
        TRUE,
        FALSE
    ) AS has_redeemed,

    IFF(
        first_redeem_date < first_issue_date,
        TRUE,
        FALSE
    ) AS redeem_before_issue_flag,

    _source_file,
    _source_row_number,
    _loaded_at

FROM typed