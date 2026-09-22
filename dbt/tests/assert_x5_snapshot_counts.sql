
-- ============================================================
-- X5 fixed-source snapshot contract
--
-- Purpose:
-- Verify that the five RAW tables match the validated
-- historical X5 dataset before rebuilding downstream models.
--
-- This is intentionally strict because X5 is a fixed
-- benchmark snapshot, NOT an evolving production dataset.
--
-- dbt singular test behavior:
-- 0 returned rows = PASS
-- 1+ returned rows = FAIL
-- ============================================================

WITH source_counts AS (

    SELECT
        'clients' AS source_name,
        COUNT(*) AS actual_count,
        400162 AS expected_count
    FROM {{ source('x5_raw', 'clients') }}

    UNION ALL

    SELECT
        'products',
        COUNT(*),
        43038
    FROM {{ source('x5_raw', 'products') }}

    UNION ALL

    SELECT
        'purchases',
        COUNT(*),
        45786568
    FROM {{ source('x5_raw', 'purchases') }}

    UNION ALL

    SELECT
        'uplift_train',
        COUNT(*),
        200039
    FROM {{ source('x5_raw', 'uplift_train') }}

    UNION ALL

    SELECT
        'uplift_test',
        COUNT(*),
        200123
    FROM {{ source('x5_raw', 'uplift_test') }}

)

SELECT
    source_name,
    actual_count,
    expected_count

FROM source_counts

WHERE actual_count != expected_count