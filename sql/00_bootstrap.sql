-- ============================================================
-- Retail Growth Experimentation & ML Decisioning Platform
-- Snowflake bootstrap
-- ============================================================

USE ROLE SYSADMIN;

-- ------------------------------------------------------------
-- Database
-- ------------------------------------------------------------

CREATE DATABASE IF NOT EXISTS RETAIL_GROWTH;

-- ------------------------------------------------------------
-- Raw schema
-- ------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS RETAIL_GROWTH.RAW;

-- ------------------------------------------------------------
-- Compute
-- ------------------------------------------------------------

CREATE WAREHOUSE IF NOT EXISTS RETAIL_DEV_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- ------------------------------------------------------------
-- Session defaults
-- ------------------------------------------------------------

USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;

-- ------------------------------------------------------------
-- Raw CSV format
-- ------------------------------------------------------------

CREATE FILE FORMAT IF NOT EXISTS RETAIL_GROWTH.RAW.X5_CSV_GZ
    TYPE = CSV
    COMPRESSION = AUTO
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    EMPTY_FIELD_AS_NULL = TRUE;

-- ============================================================
-- Verification
-- ============================================================

SELECT CURRENT_ROLE();
SELECT CURRENT_WAREHOUSE();
SELECT CURRENT_DATABASE();
SELECT CURRENT_SCHEMA();

SHOW WAREHOUSES LIKE 'RETAIL_DEV_WH';
SHOW SCHEMAS IN DATABASE RETAIL_GROWTH;
SHOW FILE FORMATS IN SCHEMA RETAIL_GROWTH.RAW;