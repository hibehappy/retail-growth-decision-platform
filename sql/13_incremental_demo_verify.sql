
-- ============================================================
-- Incremental ingestion verification
--
-- Run after loading BOTH demonstration batches.
--
-- Expected:
-- 8 raw rows
-- 5 trusted unique events
-- 2 quarantined source rows
-- 1 repeated event ID in the raw layer
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA INCREMENTAL_DEMO;


-- ------------------------------------------------------------
-- 1. Population reconciliation
-- ------------------------------------------------------------

SELECT

    (SELECT COUNT(*) FROM RAW_EVENTS)
        AS RAW_ROWS,

    (SELECT COUNT(*) FROM EVENTS)
        AS TRUSTED_EVENTS,

    (SELECT COUNT(*) FROM QUARANTINED_EVENTS)
        AS QUARANTINED_ROWS,

    (
        SELECT COUNT(*)
        FROM (
            SELECT EVENT_ID
            FROM RAW_EVENTS
            GROUP BY EVENT_ID
            HAVING COUNT(*) > 1
        )
    ) AS REPEATED_EVENT_IDS;


-- ------------------------------------------------------------
-- 2. Explain rejected records
-- ------------------------------------------------------------

SELECT

    EVENT_ID,
    REJECTION_REASON,
    SOURCE_FILE,
    SOURCE_ROW_NUMBER

FROM QUARANTINED_EVENTS

ORDER BY EVENT_ID;


-- ------------------------------------------------------------
-- 3. Verify unique trusted event IDs
--
-- Expected: zero rows.
-- ------------------------------------------------------------

SELECT

    EVENT_ID,
    COUNT(*) AS ROW_COUNT

FROM EVENTS

GROUP BY EVENT_ID

HAVING COUNT(*) > 1;


-- ------------------------------------------------------------
-- 4. Verify that no invalid rows entered the trusted layer
--
-- Expected: zero rows.
-- ------------------------------------------------------------

SELECT *

FROM EVENTS

WHERE
    EVENT_ID IS NULL
    OR CLIENT_ID IS NULL
    OR EVENT_TS IS NULL
    OR AMOUNT IS NULL
    OR AMOUNT < 0;