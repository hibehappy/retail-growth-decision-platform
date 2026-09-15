USE ROLE SYSADMIN;
USE WAREHOUSE RETAIL_DEV_WH;
USE DATABASE RETAIL_GROWTH;
USE SCHEMA RAW;


-- ============================================================
-- Clients
-- ============================================================

COPY INTO CLIENTS (
    client_id,
    first_issue_date,
    first_redeem_date,
    age,
    gender,
    _source_file,
    _source_row_number,
    _loaded_at
)
FROM (
    SELECT
        t.$1,
        t.$2,
        t.$3,
        t.$4,
        t.$5,
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER,
        METADATA$START_SCAN_TIME
    FROM @X5_STAGE/clients.csv.gz t
);


-- ============================================================
-- Products
-- ============================================================

COPY INTO PRODUCTS (
    product_id,
    level_1,
    level_2,
    level_3,
    level_4,
    segment_id,
    brand_id,
    vendor_id,
    netto,
    is_own_trademark,
    is_alcohol,
    _source_file,
    _source_row_number,
    _loaded_at
)
FROM (
    SELECT
        t.$1,
        t.$2,
        t.$3,
        t.$4,
        t.$5,
        t.$6,
        t.$7,
        t.$8,
        t.$9,
        t.$10,
        t.$11,
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER,
        METADATA$START_SCAN_TIME
    FROM @X5_STAGE/products.csv.gz t
);

-- ============================================================
-- Uplift Train
-- ============================================================

COPY INTO UPLIFT_TRAIN (
    client_id,
    treatment_flg,
    target,
    _source_file,
    _source_row_number,
    _loaded_at
)
FROM (
    SELECT
        t.$1,
        t.$2,
        t.$3,
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER,
        METADATA$START_SCAN_TIME
    FROM @X5_STAGE/uplift_train.csv.gz t
);

-- ============================================================
-- Uplift Test
-- ============================================================

COPY INTO UPLIFT_TEST (
    client_id,
    _source_file,
    _source_row_number,
    _loaded_at
)
FROM (
    SELECT
        t.$1,
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER,
        METADATA$START_SCAN_TIME
    FROM @X5_STAGE/uplift_test.csv.gz t
);

-- ============================================================
-- Purchases
-- ============================================================

COPY INTO PURCHASES (
    client_id,
    transaction_id,
    transaction_datetime,
    regular_points_received,
    express_points_received,
    regular_points_spent,
    express_points_spent,
    purchase_sum,
    store_id,
    product_id,
    product_quantity,
    trn_sum_from_iss,
    trn_sum_from_red,
    _source_file,
    _source_row_number,
    _loaded_at
)
FROM (
    SELECT
        t.$1,
        t.$2,
        t.$3,
        t.$4,
        t.$5,
        t.$6,
        t.$7,
        t.$8,
        t.$9,
        t.$10,
        t.$11,
        t.$12,
        t.$13,
        METADATA$FILENAME,
        METADATA$FILE_ROW_NUMBER,
        METADATA$START_SCAN_TIME
    FROM @X5_STAGE/purchases.csv.gz t
);

-- ============================================================
-- Ingestion Validation
-- ============================================================

SELECT 'CLIENTS' AS table_name, COUNT(*) AS row_count
FROM CLIENTS

UNION ALL

SELECT 'PRODUCTS', COUNT(*)
FROM PRODUCTS

UNION ALL

SELECT 'UPLIFT_TRAIN', COUNT(*)
FROM UPLIFT_TRAIN

UNION ALL

SELECT 'UPLIFT_TEST', COUNT(*)
FROM UPLIFT_TEST

UNION ALL

SELECT 'PURCHASES', COUNT(*)
FROM PURCHASES;