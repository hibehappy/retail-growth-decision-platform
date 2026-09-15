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

## Current Warehouse Status

The five source files are now loaded from private AWS S3 storage into the Snowflake `RETAIL_GROWTH.RAW` schema through a storage integration and external stage.

The raw layer preserves source values without destructive cleaning and includes ingestion lineage metadata such as source filename, source row number, and load timestamp.

Snowflake row counts match the source audit.

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

Missing values: **1,572** (\~3.65%)

Unique observed values: **116**

### `brand_id`

Hashed brand identifier.

Raw type: `object`

Missing values: **5,200** (\~12.08%)

Unique observed values: **4,296**

### `vendor_id`

Hashed vendor identifier.

Raw type: `object`

Missing values: **34** (\~0.08%)

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

The complete purchase source contains:

- Total raw rows: **45,786,568**
- Full transaction timestamp range:
  - Minimum: `2018-11-21 21:02:33`
  - Maximum: `2019-03-18 23:40:03`
- Purchase client IDs missing from `clients`: **0**
- Purchase product IDs missing from `products`: **0**
- Invalid transaction timestamps: **0**

Missing values:

- `trn_sum_from_red`: **42,743,212** (~93.35%)
- All other purchase columns: **0**

Snowflake full-table validation established:

- Distinct raw `transaction_id` values: **8,045,201**
- Validated customer transactions at `(transaction_id, client_id)` grain: **8,045,229**
- `transaction_id` values reused across distinct customers: **28**
- Duplicate `(transaction_id, product_id)` combinations: **3**
- Duplicate `(transaction_id, client_id, product_id)` combinations: **0**

This means `transaction_id` alone is not a globally unique transaction key.

## Validated Grains

### Transaction grain

**One row per `(transaction_id, client_id)` pair.**

Full-table validation confirmed that the following fields are internally consistent at this composite grain:

- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`

A later dbt model should create a stable surrogate `transaction_key` from the validated source business key rather than using `transaction_id` alone.

### Transaction-item grain

**One row per `(transaction_id, client_id, product_id)` combination.**

Full-table duplicate count at this grain: **0**

This is the validated business grain for product-line records.

## Referential Integrity

Full-table validation confirms:

- `purchases.client_id` → `clients.client_id`: **0 orphan client IDs**
- `purchases.product_id` → `products.product_id`: **0 orphan product IDs**

These relationships should become dbt relationship tests.

## Columns

### `client_id`

Customer associated with the transaction.

Raw type: `object / string`

Foreign key: `clients.client_id`

Important:

`client_id` is part of the validated transaction business key because some `transaction_id` values are reused across customers.

### `transaction_id`

Source transaction/basket identifier.

Raw type: `object / string`

Important:

- It is repeated across product rows within a transaction.
- It is **not globally unique across customer transactions**.
- **28** source transaction IDs are reused across different customers.

Do not use `transaction_id` alone as the primary key of the transaction fact or as the only join key to transaction items.

### `transaction_datetime`

Timestamp of the purchase transaction.

Raw type: `object`

Intended warehouse type: `TIMESTAMP`

Full observed range:

- Minimum: `2018-11-21 21:02:33`
- Maximum: `2019-03-18 23:40:03`

Full-table validation confirms this is stable within `(transaction_id, client_id)`.

### `regular_points_received`

Regular loyalty points received.

Raw type: `float64`

Full-table validation confirms this is a transaction-level field repeated across product-line rows.

Observed loyalty behavior at transaction grain:

- Points received are positive when earned.
- **98.13%** of transactions earn regular or express points.
- Average regular points received per transaction: **3.88**

### `express_points_received`

Express/promotional loyalty points received.

Raw type: `float64`

Full-table validation confirms this is a transaction-level field repeated across product-line rows.

Observed loyalty behavior:

- Points received are positive when earned.
- Average express points received per transaction: **0.04**

### `regular_points_spent`

Regular loyalty points spent/redeemed.

Raw type: `float64`

Full-table validation confirms this is a transaction-level field repeated across product-line rows.

Important source convention:

- Redemption is stored as a **negative** value.
- Minimum observed transaction-level value: **-5,066**
- Maximum observed transaction-level value: **0**
- Transactions with negative regular-point spend: **495,331**
- Transactions with positive regular-point spend: **0**

For analytics, preserve the raw negative field and derive a positive redemption amount separately, for example:

`regular_points_redeemed = ABS(regular_points_spent)` when `regular_points_spent < 0`.

Average regular points redeemed when used: **59.31**

### `express_points_spent`

Express/promotional loyalty points spent/redeemed.

Raw type: `float64`

Full-table validation confirms this is a transaction-level field repeated across product-line rows.

Important source convention:

- Redemption is stored as a **negative** value.
- Minimum observed transaction-level value: **-300**
- Maximum observed transaction-level value: **0**
- Transactions with negative express-point spend: **90,469**
- Transactions with positive express-point spend: **0**

Average express points redeemed when used: **28.39**

Across regular and express points, **6.27%** of transactions contain at least one redemption.

### `purchase_sum`

Transaction monetary amount.

Raw type: `float64`

Full-table validation confirms this is stable within `(transaction_id, client_id)` and repeated across product rows.

Important:

Because `purchase_sum` is repeated across product rows, summing it directly at raw transaction-item grain would overcount total purchase value.

This field belongs in a transaction-level fact table.

The source does not provide a validated product-level allocation of `purchase_sum`, so product/category revenue should not be inferred from this field.

### `store_id`

Store identifier associated with the transaction.

Raw type: `object / string`

Full business profiling observed **13,882** distinct stores.

No descriptive store metadata is currently available beyond the identifier, so a separate `dim_store` is not yet justified.

### `product_id`

Product associated with the line item.

Raw type: `object / string`

Foreign key: `products.product_id`

Part of the validated transaction-item grain.

### `product_quantity`

Quantity of the product purchased.

Raw type: `float64`

This is an item-level measure.

### `trn_sum_from_iss`

Numeric transaction-item-related field.

Raw type: `float64`

Observed behavior:

- Varies within most transactions.
- Full-table behavior confirms it should remain at item grain.
- It should not be collapsed into the transaction fact.

Exact business semantics remain unresolved.

### `trn_sum_from_red`

Numeric transaction-item-related field.

Raw type: `float64`

Missing values in full dataset: **42,743,212** (~93.35%)

Observed behavior:

- Highly sparse.
- Can vary within a transaction.
- Does not reliably reconcile with `purchase_sum`.

Exact business semantics remain unresolved.

## Transaction-Level vs Item-Level Structure

The raw `purchases` source contains two logical grains.

Validated transaction-level fields:

- `transaction_id`
- `client_id`
- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`

Validated transaction-item-level fields:

- `transaction_id`
- `client_id`
- `product_id`
- `product_quantity`
- `trn_sum_from_iss`
- `trn_sum_from_red`

The transaction fact must use the composite business grain `(transaction_id, client_id)` or a surrogate key derived from it. The transaction-item fact must retain the corresponding transaction key plus `product_id`.

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

        \+

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

# 8. Current Data Quality and Warehouse Validation Findings

1. Primary source keys are unique for:
   - `clients.client_id`
   - `products.product_id`
   - `uplift_train.client_id`
   - `uplift_test.client_id`

2. Train and test are mutually exclusive and collectively cover all **400,162** clients.

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
   - **42,743,212** missing `trn_sum_from_red` values

10. `transaction_id` alone is not a globally unique transaction key:
    - Distinct `transaction_id` values: **8,045,201**
    - Validated `(transaction_id, client_id)` transactions: **8,045,229**
    - Reused source transaction IDs across customers: **28**

11. Validated transaction grain:
    - `(transaction_id, client_id)`
    - All tested transaction-level attributes are consistent at this grain.

12. Validated transaction-item grain:
    - `(transaction_id, client_id, product_id)`
    - Full-table duplicate count: **0**

13. `purchase_sum` and all four loyalty-point fields are transaction-level values repeated across product rows and must not be summed at raw item grain.

14. Loyalty-point redemption uses a negative source convention:
    - received/earned points are positive
    - spent/redeemed points are negative
    - **98.13%** of transactions earn points
    - **6.27%** of transactions redeem points

15. `trn_sum_from_iss` and `trn_sum_from_red` remain item-level fields. Their exact business semantics are still unresolved.

16. The Snowflake raw layer has been loaded from S3 and preserves source-level lineage metadata.

---

# 9. Business Profiling Summary

Full-table Snowflake analysis at the validated grains produced:

## Transaction and customer profile

- Validated transactions: **8,045,229**
- Purchasing customers: **400,162**
- Total purchase value: **3,444,393,840.48**
- Average basket value: **428.13**
- Average product lines per transaction: **5.69**
- Average unique products per transaction: **5.69**
- Average units per transaction: **7.10**

All **400,162** clients appear in the historical purchase data.

## Customer behavior

- Average transactions per customer: **20.10**
- Median transactions per customer: **15**
- Repeat-customer rate: **98.07%**
- Average customer spend: **8,607.50**
- Median customer spend: **6,111.35**
- Average of customer-level average basket values: **496.31**

The high repeat rate supports behavioral feature engineering such as recency, frequency, spend, basket behavior, category affinity, and loyalty behavior.

## Temporal behavior

- Historical purchase activity spans **118 calendar dates**
- Daily transaction volume, active customers, purchase value, and average basket value vary materially across the observation window

This supports a future `mart_purchase_daily` and time-based customer features.

## Product/category behavior

- `level_1` contains **3 non-null categories**
- A null category group is produced by the **3 products** with missing `level_1`

Category analysis should use transaction presence, customers, products, and quantity rather than attributing transaction-level `purchase_sum` to products.

## Store behavior

- Distinct stores: **13,882**
- Store transaction volume and basket behavior vary materially

However, because the dataset currently provides only an anonymous `store_id` and no descriptive store attributes, `store_id` should remain on `fact_transaction` for now rather than creating an otherwise empty store dimension.

---

# 10. Validated Warehouse Model

The full-table Snowflake validation confirms that the raw purchase source should be split into separate transaction-level and item-level facts.

```text
                         dim_customer
                              |
                 +------------+-------------+
                 |                          |
                 v                          v
          fact_transaction       fact_treatment_outcome
                 |
                 | transaction_key
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
- explicit quality flags for invalid values

## `dim_product`

Grain: **one row per product**

Primary source: `products`

Purpose:

- product hierarchy
- segment/brand/vendor metadata
- product flags

## `fact_transaction`

Grain: **one row per `(transaction_id, client_id)`**

Primary source: transaction-level attributes from `purchases`

Key design:

- create a surrogate `transaction_key` from the validated composite source key
- retain the original `transaction_id` and `client_id` for lineage

Expected fields:

- `transaction_key`
- `transaction_id`
- `client_id`
- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`
- derived positive redemption measures such as `regular_points_redeemed` and `express_points_redeemed`

## `fact_transaction_item`

Grain: **one row per `(transaction_id, client_id, product_id)`**

Primary source: item-level attributes from `purchases`

Expected fields:

- `transaction_key`
- `transaction_id`
- `client_id`
- `product_id`
- `product_quantity`
- `trn_sum_from_iss`
- `trn_sum_from_red`

The fact should join to `fact_transaction` through `transaction_key`, not `transaction_id` alone.

## `fact_treatment_outcome`

Grain: **one row per uplift-training client**

Primary source: `uplift_train`

Expected fields:

- `client_id`
- `treatment_flg`
- `target`

## Date and store design

- `dim_date`: analytically useful and a reasonable future dimension because the project includes daily marts, monitoring, and time-based modeling.
- `dim_store`: deferred for now because the source contains only anonymous `store_id` values and no descriptive store metadata.

## Planned analytical marts

- `mart_customer_360`
- `mart_customer_activity`
- `mart_product_performance`
- `mart_purchase_daily`
- `mart_customer_features`
- `mart_uplift_training`

---

# 11. Deferred Decisions

The raw audit and Snowflake full-table validation are complete. Remaining decisions are intentionally deferred to the transformation/modeling stages:

- Confirm exact business semantics of:
  - `netto`
  - `trn_sum_from_iss`
  - `trn_sum_from_red`

- Define the final cleaning rule for invalid ages.

- Define how to handle the **536** redemption-before-issue anomalies.

- Decide the exact implementation and naming of the dbt-generated `transaction_key`.

- Decide whether to materialize `dim_date` immediately or when daily/feature marts are introduced.

- Revisit `dim_store` only if additional store metadata becomes available or store-level modeling requires a dedicated dimension.

- Establish treatment-assignment assumptions before making causal claims.

---
