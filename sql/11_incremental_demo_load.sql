
-- ============================================================
-- Incremental file loading
--
-- Purpose:
-- Load new S3 files into the raw landing table.
--
-- Execute each COPY when its corresponding file is present.
--
-- Do not use FORCE = TRUE for normal ingestion.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA INCREMENTAL_DEMO;


-- ------------------------------------------------------------
-- Batch 01
--
-- Map the five CSV fields by position.
-- Preserve the originating filename and source row.
--
-- METADATA$START_SCAN_TIME records the file scan time.
-- ------------------------------------------------------------

COPY INTO RAW_EVENTS (
    EVENT_ID,
    CLIENT_ID,
    EVENT_TS,
    AMOUNT,
    SCHEMA_VERSION,
    SOURCE_FILE,
    SOURCE_ROW_NUMBER,
    LOADED_AT
)

FROM (

    SELECT
        T.$1,
        T.$2,
        T.$3,
        T.$4,
        T.$5,
        T.METADATA$FILENAME,
        T.METADATA$FILE_ROW_NUMBER,
        T.METADATA$START_SCAN_TIME

    FROM @DEMO_EVENTS_STAGE T

)

FILES = ('batch_01.csv')
ON_ERROR = 'ABORT_STATEMENT';


-- ------------------------------------------------------------
-- Batch 02
--
-- Run this later, after uploading batch_02.csv.
--
-- The raw layer retains repeated events and invalid values.
-- Deduplication and validation happen downstream.
-- ------------------------------------------------------------

COPY INTO RAW_EVENTS (
    EVENT_ID,
    CLIENT_ID,
    EVENT_TS,
    AMOUNT,
    SCHEMA_VERSION,
    SOURCE_FILE,
    SOURCE_ROW_NUMBER,
    LOADED_AT
)

FROM (

    SELECT
        T.$1,
        T.$2,
        T.$3,
        T.$4,
        T.$5,
        T.METADATA$FILENAME,
        T.METADATA$FILE_ROW_NUMBER,
        T.METADATA$START_SCAN_TIME

    FROM @DEMO_EVENTS_STAGE T

)

FILES = ('batch_02.csv')
ON_ERROR = 'ABORT_STATEMENT';