
-- ============================================================
-- Incremental ingestion setup
--
-- Purpose:
-- Create an isolated Snowflake environment for synthetic
-- incoming events.
--
-- The original X5 RAW tables and dbt marts are untouched.
-- ============================================================

USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;

CREATE SCHEMA IF NOT EXISTS RETAIL_GROWTH.INCREMENTAL_DEMO;

USE DATABASE RETAIL_GROWTH;
USE SCHEMA INCREMENTAL_DEMO;


-- ------------------------------------------------------------
-- 1. Dedicated CSV file format
--
-- This demonstration uses five source fields.
-- Header validation is performed before uploading.
-- ------------------------------------------------------------

CREATE FILE FORMAT IF NOT EXISTS DEMO_CSV
    TYPE = CSV
    COMPRESSION = AUTO
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    EMPTY_FIELD_AS_NULL = TRUE;


-- ------------------------------------------------------------
-- 2. External stage
--
-- Reuse the existing secure S3 storage integration.
--
-- IMPORTANT:
-- Replace the bucket placeholder before executing.
-- ------------------------------------------------------------

CREATE STAGE IF NOT EXISTS DEMO_EVENTS_STAGE
    URL = 's3://<S3_BUCKET>/raw/x5/incremental_demo/'
    STORAGE_INTEGRATION = X5_S3_INT
    FILE_FORMAT = DEMO_CSV;


-- ------------------------------------------------------------
-- 3. Raw landing table
--
-- Preserve all source fields as VARCHAR.
-- Do not discard an entire row simply because its amount
-- or timestamp cannot be parsed.
--
-- Source metadata allows us to trace a record back to
-- its original file and row number.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS RAW_EVENTS (

    EVENT_ID VARCHAR,
    CLIENT_ID VARCHAR,
    EVENT_TS VARCHAR,
    AMOUNT VARCHAR,
    SCHEMA_VERSION VARCHAR,

    SOURCE_FILE VARCHAR,
    SOURCE_ROW_NUMBER NUMBER,
    LOADED_AT TIMESTAMP_LTZ

);


-- ------------------------------------------------------------
-- 4. Trusted event table
--
-- Only validated records should enter this table.
-- EVENT_ID represents the intended business key.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS EVENTS (

    EVENT_ID VARCHAR,
    CLIENT_ID VARCHAR,
    EVENT_TS TIMESTAMP_NTZ,
    AMOUNT NUMBER(12, 2),

    SOURCE_FILE VARCHAR,
    LOADED_AT TIMESTAMP_LTZ

);


-- ------------------------------------------------------------
-- 5. Quarantine table
--
-- Preserve invalid records and explain why they failed.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS QUARANTINED_EVENTS (

    EVENT_ID VARCHAR,
    CLIENT_ID VARCHAR,
    EVENT_TS VARCHAR,
    AMOUNT VARCHAR,
    SCHEMA_VERSION VARCHAR,

    SOURCE_FILE VARCHAR,
    SOURCE_ROW_NUMBER NUMBER,

    REJECTION_REASON VARCHAR,
    QUARANTINED_AT TIMESTAMP_LTZ

);


-- ------------------------------------------------------------
-- 6. Verify access to the external stage.
-- ------------------------------------------------------------

LIST @DEMO_EVENTS_STAGE;