SELECT
    client_id,

    TRY_TO_NUMBER(treatment_flg)::INTEGER
        AS treatment_flg,

    TRY_TO_NUMBER(target)::INTEGER
        AS target,

    _source_file,
    _source_row_number,
    _loaded_at

FROM {{ source('x5_raw', 'uplift_train') }}