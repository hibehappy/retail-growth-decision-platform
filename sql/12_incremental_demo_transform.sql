
-- ============================================================
--  Validate and promote incremental events
--
-- Purpose:
-- 1. Parse raw fields.
-- 2. Classify invalid records.
-- 3. Quarantine rejected records.
-- 4. Promote valid unique events.
--
-- Designed to be rerunnable without creating duplicate
-- business events.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA INCREMENTAL_DEMO;


-- ============================================================
-- 1. Parse the source fields
--
-- TRY_TO_* returns NULL when conversion fails rather
-- than aborting the query.
-- ============================================================

CREATE OR REPLACE VIEW V_PARSED_EVENTS AS

SELECT

    EVENT_ID,
    CLIENT_ID,
    EVENT_TS,
    AMOUNT,
    SCHEMA_VERSION,

    SOURCE_FILE,
    SOURCE_ROW_NUMBER,
    LOADED_AT,

    TRY_TO_TIMESTAMP_NTZ(EVENT_TS)
        AS PARSED_EVENT_TS,

    TRY_TO_DECIMAL(AMOUNT, 12, 2)
        AS PARSED_AMOUNT

FROM RAW_EVENTS;


-- ============================================================
-- 2. Classify records
--
-- Check required IDs, schema version, timestamp, and amount.
--
-- Also detect conflicting duplicates:
-- the same event ID appearing with different source values.
--
-- Exact duplicate events are allowed into the valid
-- candidate population and removed during promotion.
-- ============================================================

CREATE OR REPLACE VIEW V_CLASSIFIED_EVENTS AS

WITH CONFLICTING_IDS AS (

    SELECT
        EVENT_ID

    FROM V_PARSED_EVENTS

    WHERE NULLIF(TRIM(EVENT_ID), '') IS NOT NULL

    GROUP BY EVENT_ID

    HAVING
        COUNT(DISTINCT CLIENT_ID) > 1
        OR COUNT(DISTINCT EVENT_TS) > 1
        OR COUNT(DISTINCT AMOUNT) > 1
        OR COUNT(DISTINCT SCHEMA_VERSION) > 1

)

SELECT

    P.*,

    CASE

        WHEN NULLIF(TRIM(P.EVENT_ID), '') IS NULL
            THEN 'MISSING_EVENT_ID'

        WHEN NULLIF(TRIM(P.CLIENT_ID), '') IS NULL
            THEN 'MISSING_CLIENT_ID'

        WHEN P.SCHEMA_VERSION IS NULL
            OR P.SCHEMA_VERSION <> '1'
            THEN 'UNSUPPORTED_SCHEMA_VERSION'

        WHEN P.PARSED_EVENT_TS IS NULL
            THEN 'INVALID_EVENT_TIMESTAMP'

        WHEN P.PARSED_AMOUNT IS NULL
            OR P.PARSED_AMOUNT < 0
            THEN 'INVALID_AMOUNT'

        WHEN C.EVENT_ID IS NOT NULL
            THEN 'CONFLICTING_EVENT_ID'

        ELSE NULL

    END AS REJECTION_REASON

FROM V_PARSED_EVENTS P

LEFT JOIN CONFLICTING_IDS C
    ON P.EVENT_ID = C.EVENT_ID;


-- ============================================================
-- 3. Quarantine rejected source rows
--
-- The source-file/row combination identifies a specific
-- physical record in our append-only demonstration files.
--
-- Re-running this MERGE does not insert the same rejected
-- source row again.
-- ============================================================

MERGE INTO QUARANTINED_EVENTS AS TARGET

USING (

    SELECT *

    FROM V_CLASSIFIED_EVENTS

    WHERE REJECTION_REASON IS NOT NULL

) AS SOURCE

ON
    TARGET.SOURCE_FILE = SOURCE.SOURCE_FILE
    AND TARGET.SOURCE_ROW_NUMBER = SOURCE.SOURCE_ROW_NUMBER

WHEN NOT MATCHED THEN

    INSERT (

        EVENT_ID,
        CLIENT_ID,
        EVENT_TS,
        AMOUNT,
        SCHEMA_VERSION,
        SOURCE_FILE,
        SOURCE_ROW_NUMBER,
        REJECTION_REASON,
        QUARANTINED_AT

    )

    VALUES (

        SOURCE.EVENT_ID,
        SOURCE.CLIENT_ID,
        SOURCE.EVENT_TS,
        SOURCE.AMOUNT,
        SOURCE.SCHEMA_VERSION,
        SOURCE.SOURCE_FILE,
        SOURCE.SOURCE_ROW_NUMBER,
        SOURCE.REJECTION_REASON,
        CURRENT_TIMESTAMP()

    );


-- ============================================================
-- 4. Promote valid events
--
-- Keep one deterministic source row per event ID.
--
-- WHEN NOT MATCHED ensures an event already present in
-- the trusted table is not inserted again.
--
-- We intentionally do not overwrite existing events.
-- Changes/corrections require a separate reconciliation
-- policy rather than an implicit last-write-wins rule.
-- ============================================================

MERGE INTO EVENTS AS TARGET

USING (

    SELECT

        EVENT_ID,
        CLIENT_ID,

        PARSED_EVENT_TS AS EVENT_TS,
        PARSED_AMOUNT AS AMOUNT,

        SOURCE_FILE,
        LOADED_AT

    FROM V_CLASSIFIED_EVENTS

    WHERE REJECTION_REASON IS NULL

    QUALIFY ROW_NUMBER() OVER (

        PARTITION BY EVENT_ID

        ORDER BY
            SOURCE_FILE,
            SOURCE_ROW_NUMBER

    ) = 1

) AS SOURCE

ON TARGET.EVENT_ID = SOURCE.EVENT_ID

WHEN NOT MATCHED THEN

    INSERT (

        EVENT_ID,
        CLIENT_ID,
        EVENT_TS,
        AMOUNT,
        SOURCE_FILE,
        LOADED_AT

    )

    VALUES (

        SOURCE.EVENT_ID,
        SOURCE.CLIENT_ID,
        SOURCE.EVENT_TS,
        SOURCE.AMOUNT,
        SOURCE.SOURCE_FILE,
        SOURCE.LOADED_AT

    );