-- ============================================================
-- dbt development permissions
-- ============================================================

USE ROLE ACCOUNTADMIN;

CREATE ROLE IF NOT EXISTS DBT_DEV_ROLE;

-- Allow the developer to assume the dbt role.
GRANT ROLE DBT_DEV_ROLE
TO USER <SNOWFLAKE_USER>;

-- Keep the custom role beneath SYSADMIN in the role hierarchy.
GRANT ROLE DBT_DEV_ROLE
TO ROLE SYSADMIN;

-- Compute
GRANT USAGE
ON WAREHOUSE RETAIL_DEV_WH
TO ROLE DBT_DEV_ROLE;

-- Database access
GRANT USAGE
ON DATABASE RETAIL_GROWTH
TO ROLE DBT_DEV_ROLE;

-- dbt will create development schemas such as
-- DEV_STAGING and DEV_CORE.
GRANT CREATE SCHEMA
ON DATABASE RETAIL_GROWTH
TO ROLE DBT_DEV_ROLE;

-- Read-only access to raw source data.
GRANT USAGE
ON SCHEMA RETAIL_GROWTH.RAW
TO ROLE DBT_DEV_ROLE;

GRANT SELECT
ON ALL TABLES IN SCHEMA RETAIL_GROWTH.RAW
TO ROLE DBT_DEV_ROLE;

GRANT SELECT
ON FUTURE TABLES IN SCHEMA RETAIL_GROWTH.RAW
TO ROLE DBT_DEV_ROLE;