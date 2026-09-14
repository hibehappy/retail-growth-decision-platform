# X5 RetailHero Data Dictionary

## Dataset Overview

The X5 RetailHero dataset contains customer demographics, product metadata, historical purchase behavior, and uplift-modeling treatment/outcome data.

The core source relationships are:

```text
clients
  |
  | client_id
  |
  +--------------------------+
  |                          |
  v                          v
purchases              uplift_train / uplift_test
  |
  | product_id
  v
products
```

Verified client split:

- Total clients: **400,162**
- Uplift train clients: **200,039**
- Uplift test clients: **200,123**
- Train/test overlap: **0**
- Clients missing from train/test: **0**
- Train/test IDs missing from clients: **0**

Therefore, `uplift_train` and `uplift_test` form a complete, non-overlapping partition of the `clients` table.

---

# 1. `clients`

## Purpose

Contains one record per customer with demographic and loyalty-program information.

## Grain

**One row per client.**

## Primary Key

`client_id`

## Validation

- Rows: **400,162**
- Unique `client_id`: **400,162**
- Duplicate `client_id`: **0**
- Duplicate rows: **0**

## Columns

### `client_id`

Unique customer identifier.

Raw type: `object / string`

Constraints:

- Not null
- Unique

### `first_issue_date`

Timestamp associated with the customer's first loyalty-program issue event.

Raw type: `object`

Intended warehouse type: `TIMESTAMP`

Observed range:

- Minimum: `2017-04-04 18:24:18`
- Maximum: `2019-03-15 21:50:56`

Missing values: **0**

### `first_redeem_date`

Timestamp associated with the customer's first redemption event.

Raw type: `object`

Intended warehouse type: `TIMESTAMP`

Observed range among non-null records:

- Minimum: `2017-04-11 09:42:20`
- Maximum: `2019-11-20 01:14:10`

Missing values: **35,469**

Additional quality finding:

- **536** clients have a `first_redeem_date` earlier than `first_issue_date`
- This is a small anomaly and should be flagged rather than silently corrected

Important:

A missing redemption date should not automatically be treated as an error; it may indicate that the client had not yet redeemed.

Potential derived features:

- `has_redeemed`
- `redeem_delay_days`
- `redeem_before_issue_flag`

### `age`

Customer age.

Raw type: `int64`

Missing values: **0**

Observed summary:

- Minimum: **-7491**
- Median: **45**
- 25th percentile: **34**
- 75th percentile: **59**
- Maximum: **1901**

The central distribution is plausible, but the field contains obvious invalid values.

Important:

Raw values should be preserved. A later cleaned layer should create a validated/nullable age field and an explicit invalid-age flag rather than overwriting the source.

### `gender`

Categorical customer gender code.

Raw type: `object`

Missing values: **0**

Observed values:

- `U`: **185,706**
- `F`: **147,649**
- `M`: **66,807**

Observed proportions:

- `U`: **46.41%**
- `F`: **36.90%**
- `M`: **16.69%**

The exact semantic meaning of `U` should not be expanded beyond the source code without authoritative documentation.

---

# 2. `products`

## Purpose

Contains product-level metadata and hierarchical product attributes.

## Grain

**One row per product.**

## Primary Key

`product_id`

## Validation

- Rows: **43,038**
- Unique `product_id`: **43,038**
- Duplicate `product_id`: **0**
- Duplicate rows: **0**

## Columns

### `product_id`

Unique product identifier.

Raw type: `object / string`

Constraints:

- Not null
- Unique

### `level_1`

Highest-level hashed product hierarchy/category attribute.

Raw type: `object`

Missing values: **3**

Unique observed values: **3**

### `level_2`

Second-level hashed product hierarchy/category attribute.

Raw type: `object`

Missing values: **3**

Unique observed values: **42**

### `level_3`

Third-level hashed product hierarchy/category attribute.

Raw type: `object`

Missing values: **3**

Unique observed values: **201**

### `level_4`

Fourth-level hashed product hierarchy/category attribute.

Raw type: `object`

Missing values: **3**

Unique observed values: **790**

The `level_1` through `level_4` columns appear to form a hierarchical product classification. The exact semantic category names are anonymized.

### `segment_id`

Product segment identifier.

Raw type: `float64`

Missing values: **1,572** (~3.65%)

Unique observed values: **116**

### `brand_id`

Hashed brand identifier.

Raw type: `object`

Missing values: **5,200** (~12.08%)

Unique observed values: **4,296**

### `vendor_id`

Hashed vendor identifier.

Raw type: `object`

Missing values: **34** (~0.08%)

Unique observed values: **3,193**

### `netto`

Numeric product attribute.

Raw type: `float64`

Missing values: **3**

Unique observed values: **780**

Observed values range widely, but the precise business meaning/unit is not conclusively documented. The raw field name should be retained until an authoritative definition is established.

### `is_own_trademark`

Indicator for whether the product belongs to the retailer's own trademark/private-label group.

Raw type: `int64`

Observed domain: `{0, 1}`

Counts:

- `0`: **41,524**
- `1`: **1,514**

### `is_alcohol`

Indicator for whether the product is classified as alcohol.

Raw type: `int64`

Observed domain: `{0, 1}`

Counts:

- `0`: **40,645**
- `1`: **2,393**

---

# 3. `purchases`

## Purpose

Contains historical customer purchase behavior prior to the uplift-modeling marketing outcome period.

This is the primary behavioral source for transaction analytics, customer feature engineering, and later uplift modeling.

## Full-Table Validation

A chunked scan of the complete purchase file established:

- Total rows: **45,786,568**
- Full transaction date range:
  - Minimum: `2018-11-21 21:02:33`
  - Maximum: `2019-03-18 23:40:03`
- Purchase client IDs missing from `clients`: **0**
- Purchase product IDs missing from `products`: **0**
- Invalid transaction timestamps: **0**

Missing values:

- `trn_sum_from_red`: **42,743,212**
- All other purchase columns: **0**

## Grain

The 100,000-row audit sample supports:

**One row per product per transaction.**

Candidate composite key:

`transaction_id + product_id`

Sample validation:

- Sample rows: **100,000**
- Unique transactions: **17,292**
- Unique products: **13,524**
- Unique transaction-product pairs: **100,000**
- Duplicate transaction-product pairs: **0**
- Maximum clients associated with one transaction: **1**
- Transactions associated with more than one client: **0**

The exact full-table uniqueness of `(transaction_id, product_id)` will be verified in Snowflake, where a 45M-row group-by is more appropriate than maintaining a large in-memory set in pandas.

## Referential Integrity

Full-table validation confirms:

- `purchases.client_id` → `clients.client_id`: **0 orphan client IDs**
- `purchases.product_id` → `products.product_id`: **0 orphan product IDs**

These relationships should later become dbt relationship tests.

## Columns

### `client_id`

Customer responsible for the transaction.

Raw type: `object`

Foreign key: `clients.client_id`

### `transaction_id`

Transaction/basket identifier.

Raw type: `object`

Important:

`transaction_id` is not unique at the row level because a transaction may contain multiple products.

### `transaction_datetime`

Timestamp of the purchase transaction.

Raw type: `object`

Intended warehouse type: `TIMESTAMP`

Full observed range:

- Minimum: `2018-11-21 21:02:33`
- Maximum: `2019-03-18 23:40:03`

### `regular_points_received`

Regular loyalty points received.

Raw type: `float64`

Observed behavior:

Constant within **100% of sampled transactions**, indicating that this is a transaction-level attribute repeated across product-line rows.

### `express_points_received`

Express/promotional loyalty points received.

Raw type: `float64`

Observed behavior:

Constant within **100% of sampled transactions**.

### `regular_points_spent`

Regular loyalty points spent.

Raw type: `float64`

Observed behavior:

Constant within **100% of sampled transactions**.

### `express_points_spent`

Express/promotional loyalty points spent.

Raw type: `float64`

Observed behavior:

Constant within **100% of sampled transactions**.

### `purchase_sum`

Transaction monetary amount.

Raw type: `float64`

Observed behavior:

Constant within **100% of sampled transactions**.

Important:

Because `purchase_sum` is repeated across product rows within a transaction, summing it directly across raw purchase rows would overcount transaction value.

This field should belong in a transaction-level fact table rather than an item-level fact table.

### `store_id`

Store identifier associated with the transaction.

Raw type: `object`

### `product_id`

Product associated with the line item.

Raw type: `object`

Foreign key: `products.product_id`

### `product_quantity`

Quantity of the product purchased.

Raw type: `float64`

### `trn_sum_from_iss`

Numeric transaction-item-related field.

Raw type: `float64`

Observed behavior:

- Varies within most transactions
- Only ~14% of sampled transactions contain a single unique value

This behavior is more consistent with an item-level measure than a transaction-level measure.

Exact business semantics remain unresolved.

### `trn_sum_from_red`

Numeric transaction-item-related field.

Raw type: `float64`

Missing values in full dataset: **42,743,212** (~93.35%)

Observed behavior:

- Appears constant within many transactions, but this is heavily affected by extreme missingness
- Does not reliably reconcile with `purchase_sum`

Exact business semantics remain unresolved.

## Transaction-Level vs Item-Level Structure

The raw `purchases` source contains two logical grains.

Transaction-level fields:

- `transaction_id`
- `client_id`
- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`

Transaction-item-level fields:

- `transaction_id`
- `product_id`
- `product_quantity`
- `trn_sum_from_iss`
- `trn_sum_from_red`

This distinction drives the revised warehouse model described below.

---

# 4. `uplift_train`

## Purpose

Contains treatment assignment and observed outcome information for the training population used in uplift modeling.

## Grain

**One row per training client.**

## Primary Key

`client_id`

## Validation

- Rows: **200,039**
- Unique `client_id`: **200,039**
- Duplicate `client_id`: **0**
- Duplicate rows: **0**
- Missing values: **0**

## Columns

### `client_id`

Unique customer identifier.

Foreign key: `clients.client_id`

### `treatment_flg`

Binary treatment indicator.

Raw type: `int64`

Observed domain: `{0, 1}`

Observed counts:

- `0`: **100,058**
- `1`: **99,981**

Observed proportions:

- `0`: **50.0192%**
- `1`: **49.9808%**

The treatment/control groups are nearly perfectly balanced.

Important:

Do not describe treatment assignment as randomized unless the assignment mechanism is verified from authoritative dataset documentation.

### `target`

Binary observed outcome.

Raw type: `int64`

Observed domain: `{0, 1}`

Observed counts:

- `0`: **76,037**
- `1`: **124,002**

Observed proportions:

- `0`: **38.0111%**
- `1`: **61.9889%**

## Treatment × Outcome Distribution

| treatment_flg | target = 0 | target = 1 | Total |
|---|---:|---:|---:|
| 0 | 39,695 | 60,363 | 100,058 |
| 1 | 36,342 | 63,639 | 99,981 |
| Total | 76,037 | 124,002 | 200,039 |

Observed within-group target rates:

| Group | Target = 0 | Target = 1 |
|---|---:|---:|
| Control (`treatment_flg = 0`) | 39.6720% | 60.3280% |
| Treatment (`treatment_flg = 1`) | 36.3489% | 63.6511% |

Raw observed difference in target rate:

`63.6511% - 60.3280% = 3.3231 percentage points`

Important:

This is a descriptive difference only. It should **not** yet be described as a causal treatment effect unless the treatment-assignment assumptions required for causal interpretation are established.

---

# 5. `uplift_test`

## Purpose

Contains the client IDs from the original competition test population.

Treatment and target values are not included.

## Grain

**One row per test client.**

## Primary Key

`client_id`

## Validation

- Rows: **200,123**
- Unique `client_id`: **200,123**
- Duplicate `client_id`: **0**
- Missing `client_id`: **0**

## Columns

### `client_id`

Unique customer identifier.

Foreign key: `clients.client_id`

---

# 6. Verified Dataset Relationships

## Clients → Uplift Split

The complete client population is partitioned exactly between train and test.

Verified:

- Train/test overlap: **0**
- Train + test unique clients: **400,162**
- Clients absent from train/test: **0**
- Train/test clients absent from `clients`: **0**

Relationship:

```text
clients
  |
  |-- uplift_train
  |
  +-- uplift_test
```

## Clients → Purchases

Relationship:

`clients.client_id` → `purchases.client_id`

Full-table validation:

- Orphan purchase client IDs: **0**

## Products → Purchases

Relationship:

`products.product_id` → `purchases.product_id`

Full-table validation:

- Orphan purchase product IDs: **0**

---

# 7. Analytical Timeline

The dataset can be interpreted conceptually as:

```text
Client attributes
        +
Historical purchase behavior
        |
        v
Marketing treatment / no treatment
        |
        v
Observed target outcome
```

Historical customer features will eventually be constructed from:

- recency
- frequency
- monetary behavior
- basket behavior
- product/category behavior
- loyalty-point behavior
- customer tenure
- purchase trends

A key requirement will be preventing post-treatment information from leaking into model features.

---

# 8. Current Data Quality Findings

1. Primary keys are unique for:
   - `clients.client_id`
   - `products.product_id`
   - `uplift_train.client_id`
   - `uplift_test.client_id`

2. Train and test are mutually exclusive and collectively cover all 400,162 clients.

3. `first_redeem_date` contains **35,469** missing values.

4. **536** clients have `first_redeem_date < first_issue_date`.

5. `age` contains obvious invalid values, with observed extremes of **-7491** and **1901**.

6. Product missingness is concentrated mainly in:
   - `brand_id`: ~12.08%
   - `segment_id`: ~3.65%
   - `vendor_id`: ~0.08%

7. Product binary fields are valid:
   - `is_own_trademark ∈ {0,1}`
   - `is_alcohol ∈ {0,1}`

8. Treatment and target fields are valid binary variables.

9. The full purchase table contains:
   - **45,786,568** rows
   - **0** orphan client IDs
   - **0** orphan product IDs
   - **0** invalid timestamps

10. `trn_sum_from_red` is highly sparse:
    - **42,743,212** missing values

11. The raw purchase source mixes two grains:
    - transaction-level basket attributes
    - transaction-product line items

12. `purchase_sum` and all four loyalty-point fields are repeated transaction-level values and should not be summed at raw line-item grain.

---

# 9. Revised Candidate Warehouse Model

The raw audit shows that the purchase source should be split into separate transaction-level and item-level facts.

```text
                         dim_customer
                              |
                 +------------+-------------+
                 |                          |
                 v                          v
          fact_transaction       fact_treatment_outcome
                 |
                 | transaction_id
                 v
       fact_transaction_item
                 |
                 | product_id
                 v
             dim_product
```

## `dim_customer`

Grain: **one row per client**

Primary source: `clients`

Purpose:

- customer demographics
- loyalty-program dates
- cleaned/validated customer attributes

## `dim_product`

Grain: **one row per product**

Primary source: `products`

Purpose:

- product hierarchy
- segment/brand/vendor metadata
- product flags

## `fact_transaction`

Grain: **one row per transaction**

Primary source: deduplicated transaction-level attributes from `purchases`

Expected fields:

- `transaction_id`
- `client_id`
- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`

## `fact_transaction_item`

Grain: **one row per transaction-product pair**

Primary source: item-level attributes from `purchases`

Expected fields:

- `transaction_id`
- `product_id`
- `product_quantity`
- `trn_sum_from_iss`
- `trn_sum_from_red`

## `fact_treatment_outcome`

Grain: **one row per uplift-training client**

Primary source: `uplift_train`

Expected fields:

- `client_id`
- `treatment_flg`
- `target`

## Candidate future dimensions

- `dim_date`
- `dim_store`

These remain candidates rather than commitments until their analytical value is evaluated.

## Potential analytical marts

- `mart_customer_360`
- `mart_customer_activity`
- `mart_product_performance`
- `mart_purchase_daily`
- `mart_customer_features`
- `mart_uplift_training`

---

# 10. Deferred Decisions

The raw-data audit is essentially complete. The following questions are intentionally deferred because they are better handled in the warehouse/transformation layer:

- Verify full-table uniqueness of `(transaction_id, product_id)` in Snowflake
- Confirm exact business semantics of:
  - `netto`
  - `trn_sum_from_iss`
  - `trn_sum_from_red`
- Define the final cleaning rule for invalid ages
- Define how to handle the 536 redemption-before-issue anomalies
- Decide whether `dim_date` and `dim_store` provide enough analytical value to create explicitly
- Establish treatment-assignment assumptions before making causal claims

---

# 11. Next Step

Create a faithful **raw Snowflake layer** from the source files.

The next stage should:

1. Load the raw source tables into Snowflake without silently changing their meaning
2. Reproduce row counts and key/integrity checks in SQL
3. Validate full-table purchase grain with SQL
4. Perform business-level EDA across the complete 45.8M-row purchase table
5. Use those findings to finalize the dbt dimensional model

The purpose of the next stage is not to repeat the pandas audit. It is to move the validated source data into the system where the rest of the project will be built.
