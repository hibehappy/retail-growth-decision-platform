-- ============================================================
-- Snowflake query efficiency audit
--
-- Purpose:
--
-- Review recent queries executed on RETAIL_DEV_WH.
--
-- These metrics are efficiency indicators.
-- They are NOT exact dollar-cost calculations.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;

-- ============================================================
-- 1. Recent query activity
-- ============================================================

SELECT

    QUERY_ID,
    QUERY_TYPE,
    EXECUTION_STATUS,

    START_TIME,

    TOTAL_ELAPSED_TIME / 1000
        AS ELAPSED_SECONDS,

    BYTES_SCANNED,

    ROWS_PRODUCED,

    QUERY_TEXT

FROM TABLE(

    INFORMATION_SCHEMA
        .QUERY_HISTORY_BY_WAREHOUSE(

            WAREHOUSE_NAME =>
                'RETAIL_DEV_WH',

            END_TIME_RANGE_START =>
                DATEADD(
                    'DAY',
                    -6,
                    CURRENT_TIMESTAMP()
                ),

            END_TIME_RANGE_END =>
                CURRENT_TIMESTAMP(),

            RESULT_LIMIT =>
                1000
        )
)

WHERE USER_NAME = CURRENT_USER()

ORDER BY
    TOTAL_ELAPSED_TIME DESC;

-- ============================================================
-- 2. Aggregate efficiency summary
-- ============================================================

WITH QUERY_HISTORY AS (

    SELECT *

    FROM TABLE(

        INFORMATION_SCHEMA
            .QUERY_HISTORY_BY_WAREHOUSE(

                WAREHOUSE_NAME =>
                    'RETAIL_DEV_WH',

                END_TIME_RANGE_START =>
                    DATEADD(
                        'DAY',
                        -6,
                        CURRENT_TIMESTAMP()
                    ),

                END_TIME_RANGE_END =>
                    CURRENT_TIMESTAMP(),

                RESULT_LIMIT =>
                    1000
            )
    )

    WHERE
        USER_NAME = CURRENT_USER()
        AND EXECUTION_STATUS = 'SUCCESS'
        AND TOTAL_ELAPSED_TIME >= 0

)

SELECT

    COUNT(*) AS QUERY_COUNT,

    ROUND(
        SUM(TOTAL_ELAPSED_TIME)
        / 1000,
        2
    ) AS TOTAL_ELAPSED_SECONDS,

    ROUND(
        AVG(TOTAL_ELAPSED_TIME)
        / 1000,
        2
    ) AS AVG_ELAPSED_SECONDS,

    ROUND(
        MAX(TOTAL_ELAPSED_TIME)
        / 1000,
        2
    ) AS MAX_ELAPSED_SECONDS,

    ROUND(
        SUM(BYTES_SCANNED)
        / POWER(1024, 3),
        3
    ) AS TOTAL_GB_SCANNED,

    ROUND(
        MAX(BYTES_SCANNED)
        / POWER(1024, 3),
        3
    ) AS MAX_GB_SCANNED,

    ROUND(
        AVG(BYTES_SCANNED)
        / POWER(1024, 2),
        3
    ) AS AVG_MB_SCANNED

FROM QUERY_HISTORY;

-- ============================================================
-- 3. Largest scans
-- ============================================================

SELECT

    QUERY_ID,

    QUERY_TYPE,

    ROUND(
        BYTES_SCANNED
        / POWER(1024, 3),
        3
    ) AS GB_SCANNED,

    ROUND(
        TOTAL_ELAPSED_TIME
        / 1000,
        2
    ) AS ELAPSED_SECONDS,

    START_TIME,

    QUERY_TEXT

FROM TABLE(

    INFORMATION_SCHEMA
        .QUERY_HISTORY_BY_WAREHOUSE(

            WAREHOUSE_NAME =>
                'RETAIL_DEV_WH',

            END_TIME_RANGE_START =>
                DATEADD(
                    'DAY',
                    -6,
                    CURRENT_TIMESTAMP()
                ),

            RESULT_LIMIT =>
                1000
        )
)

WHERE
    USER_NAME = CURRENT_USER()
    AND BYTES_SCANNED > 0

ORDER BY
    BYTES_SCANNED DESC

LIMIT 20;