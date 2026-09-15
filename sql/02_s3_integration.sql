-- ============================================================
-- S3 Storage Integration
-- ============================================================

USE ROLE ACCOUNTADMIN;

CREATE STORAGE INTEGRATION IF NOT EXISTS X5_S3_INT
    TYPE = EXTERNAL_STAGE
    STORAGE_PROVIDER = 'S3'
    ENABLED = TRUE
    STORAGE_AWS_ROLE_ARN = '<AWS_ROLE_ARN>'
    STORAGE_ALLOWED_LOCATIONS = (
        's3://<S3_BUCKET>/raw/x5/'
    );

DESC INTEGRATION X5_S3_INT;

-- ============================================================
-- Verification
-- ============================================================

SELECT SYSTEM$VALIDATE_STORAGE_INTEGRATION(
    'X5_S3_INT',
    's3://<S3_BUCKET>/raw/x5/',
    'unused.txt',
    'list'
);

-- ============================================================
-- External Stage
-- ============================================================

USE ROLE SYSADMIN;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;

CREATE STAGE IF NOT EXISTS X5_STAGE
    STORAGE_INTEGRATION = X5_S3_INT
    URL = 's3://<S3_BUCKET>/raw/x5/'
    FILE_FORMAT = X5_CSV_GZ;

-- ============================================================
-- Verification
-- ============================================================

LIST @X5_STAGE;

SELECT
    t.$1,
    t.$2,
    t.$3,
    t.$4,
    t.$5,
    METADATA$FILENAME,
    METADATA$FILE_ROW_NUMBER
FROM @X5_STAGE/clients.csv.gz t
LIMIT 10;