SELECT
    client_id,

    _source_file,
    _source_row_number,
    _loaded_at

FROM {{ source('x5_raw', 'uplift_test') }}