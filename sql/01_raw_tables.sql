USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;


-- ============================================================
-- Clients
-- ============================================================

CREATE TABLE IF NOT EXISTS CLIENTS (
    client_id VARCHAR,
    first_issue_date VARCHAR,
    first_redeem_date VARCHAR,
    age VARCHAR,
    gender VARCHAR,

    _source_file VARCHAR,
    _source_row_number NUMBER,
    _loaded_at TIMESTAMP_LTZ
);


-- ============================================================
-- Products
-- ============================================================

CREATE TABLE IF NOT EXISTS PRODUCTS (
    product_id VARCHAR,
    level_1 VARCHAR,
    level_2 VARCHAR,
    level_3 VARCHAR,
    level_4 VARCHAR,
    segment_id VARCHAR,
    brand_id VARCHAR,
    vendor_id VARCHAR,
    netto VARCHAR,
    is_own_trademark VARCHAR,
    is_alcohol VARCHAR,

    _source_file VARCHAR,
    _source_row_number NUMBER,
    _loaded_at TIMESTAMP_LTZ
);


-- ============================================================
-- Purchases
-- ============================================================

CREATE TABLE IF NOT EXISTS PURCHASES (
    client_id VARCHAR,
    transaction_id VARCHAR,
    transaction_datetime VARCHAR,
    regular_points_received VARCHAR,
    express_points_received VARCHAR,
    regular_points_spent VARCHAR,
    express_points_spent VARCHAR,
    purchase_sum VARCHAR,
    store_id VARCHAR,
    product_id VARCHAR,
    product_quantity VARCHAR,
    trn_sum_from_iss VARCHAR,
    trn_sum_from_red VARCHAR,

    _source_file VARCHAR,
    _source_row_number NUMBER,
    _loaded_at TIMESTAMP_LTZ
);


-- ============================================================
-- Uplift Train
-- ============================================================

CREATE TABLE IF NOT EXISTS UPLIFT_TRAIN (
    client_id VARCHAR,
    treatment_flg VARCHAR,
    target VARCHAR,

    _source_file VARCHAR,
    _source_row_number NUMBER,
    _loaded_at TIMESTAMP_LTZ
);


-- ============================================================
-- Uplift Test
-- ============================================================

CREATE TABLE IF NOT EXISTS UPLIFT_TEST (
    client_id VARCHAR,

    _source_file VARCHAR,
    _source_row_number NUMBER,
    _loaded_at TIMESTAMP_LTZ
);

-- ============================================================
-- Verification
-- ============================================================

SELECT CURRENT_WAREHOUSE();
SELECT CURRENT_DATABASE();
SELECT CURRENT_SCHEMA();
SHOW TABLES IN SCHEMA RETAIL_GROWTH.RAW;