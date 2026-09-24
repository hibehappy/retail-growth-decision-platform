# X5 RetailHero Data Dictionary

## Purpose

This document defines the source datasets, validated grains, important fields, warehouse models, analytical marts, model-feature groups, and known data-quality limitations used throughout the Retail Growth Decision Platform.

Definitions are based on the source data and transformations implemented in this repository. Where source-field semantics could not be verified, the field is explicitly marked as unresolved rather than assigned an inferred meaning.

Synthetic incremental-ingestion and streaming datasets are documented separately at the end of this file and are not part of the historical X5 modeling population.

## Dataset overview

The X5 RetailHero dataset contains customer demographics, product metadata, historical purchase behavior, and uplift-modeling treatment/outcome data.

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
- Train/test IDs missing from `clients`: **0**

Therefore, `uplift_train` and `uplift_test` form a complete, non-overlapping partition of the `clients` table.

## Warehouse status

The five historical source files are loaded from private AWS S3 storage into the Snowflake `RETAIL_GROWTH.RAW` schema through a storage integration and external stage.

The raw layer preserves source values without destructive cleaning and includes ingestion-lineage metadata such as source filename, source row number, and load timestamp.

Snowflake row counts match the source audit.

---

# 1. `clients`

## Purpose

Contains one record per customer with demographic and loyalty-program information.

## Grain

**One row per client.**

## Primary key

`client_id`

## Validation

- Rows: **400,162**
- Unique `client_id`: **400,162**
- Duplicate `client_id`: **0**
- Duplicate rows: **0**

## Columns

### `client_id`

Unique customer identifier.

Raw type: string.

Constraints:

- not null
- unique

### `first_issue_date`

Timestamp associated with the customer's first loyalty-program issue event.

Raw type: source text/date representation.

Warehouse type: timestamp.

Observed range:

- minimum: `2017-04-04 18:24:18`
- maximum: `2019-03-15 21:50:56`

Missing values: **0**.

### `first_redeem_date`

Timestamp associated with the customer's first redemption event.

Raw type: source text/date representation.

Warehouse type: timestamp.

Observed non-null range:

- minimum: `2017-04-11 09:42:20`
- maximum: `2019-11-20 01:14:10`

Missing values: **35,469**.

Additional quality finding:

- **536** clients have `first_redeem_date < first_issue_date`.

The raw value is preserved. Downstream modeling uses explicit derived fields/flags rather than silently rewriting the source.

A missing redemption date is not automatically an error; it may indicate that the client had not redeemed.

### `age`

Customer age.

Raw type: integer.

Observed summary:

- minimum: **-7,491**
- 25th percentile: **34**
- median: **45**
- 75th percentile: **59**
- maximum: **1,901**

The central distribution is plausible, but the extremes are clearly invalid. Raw values are preserved; the transformed layer should use a validated/nullable age plus an explicit quality flag rather than overwriting the source value.

### `gender`

Categorical source code.

Observed counts:

- `U`: **185,706**
- `F`: **147,649**
- `M`: **66,807**

Observed proportions:

- `U`: **46.41%**
- `F`: **36.90%**
- `M`: **16.69%**

The exact semantic expansion of `U` is not asserted without authoritative source documentation.

---

# 2. `products`

## Purpose

Contains product-level metadata and anonymized product-hierarchy attributes.

## Grain

**One row per product.**

## Primary key

`product_id`

## Validation

- Rows: **43,038**
- Unique `product_id`: **43,038**
- Duplicate `product_id`: **0**
- Duplicate rows: **0**

## Columns

### `product_id`

Unique product identifier.

Raw type: string.

Constraints:

- not null
- unique

### `level_1`

Highest-level anonymized product hierarchy/category attribute.

- missing values: **3**
- non-null unique values: **3**

### `level_2`

Second-level anonymized hierarchy attribute.

- missing values: **3**
- unique observed values: **42**

### `level_3`

Third-level anonymized hierarchy attribute.

- missing values: **3**
- unique observed values: **201**

### `level_4`

Fourth-level anonymized hierarchy attribute.

- missing values: **3**
- unique observed values: **790**

`level_1` through `level_4` behave as a hierarchical product classification, but the underlying category names are anonymized.

### `segment_id`

Product segment identifier.

- raw type: numeric/nullable
- missing values: **1,572** (~3.65%)
- unique observed values: **116**

### `brand_id`

Anonymized brand identifier.

- missing values: **5,200** (~12.08%)
- unique observed values: **4,296**

### `vendor_id`

Anonymized vendor identifier.

- missing values: **34** (~0.08%)
- unique observed values: **3,193**

### `netto`

Numeric product attribute.

- missing values: **3**
- unique observed values: **780**

**Semantics unresolved.**

The word `netto` could suggest a net weight, net price/value, or another source-specific measure, but the unit and intended business definition have not been verified for this dataset.

Do not rename this field to `net_weight`, `net_price`, or another interpreted name, convert its units, or treat it as a verified monetary measure without authoritative documentation.

### `is_own_trademark`

Binary retailer-own-trademark/private-label indicator.

Observed domain: `{0, 1}`.

Counts:

- `0`: **41,524**
- `1`: **1,514**

### `is_alcohol`

Binary alcohol classification indicator.

Observed domain: `{0, 1}`.

Counts:

- `0`: **40,645**
- `1`: **2,393**

---

# 3. `purchases`

## Purpose

Contains historical customer purchase behavior before the uplift-modeling outcome period. It is the primary behavioral source for transaction analytics, customer feature engineering, and uplift modeling.

## Full-table validation

- Raw rows: **45,786,568**
- Minimum transaction timestamp: `2018-11-21 21:02:33`
- Maximum transaction timestamp: `2019-03-18 23:40:03`
- Orphan client IDs: **0**
- Orphan product IDs: **0**
- Invalid transaction timestamps: **0**
- Missing `trn_sum_from_red`: **42,743,212** (~93.35%)
- Missing values in other purchase columns: **0**

Key-grain findings:

- Distinct raw `transaction_id`: **8,045,201**
- Validated `(transaction_id, client_id)` transactions: **8,045,229**
- `transaction_id` values reused across customers: **28**
- Duplicate `(transaction_id, product_id)` combinations: **3**
- Duplicate `(transaction_id, client_id, product_id)` combinations: **0**

`transaction_id` alone is therefore **not** a globally unique transaction key.

## Validated transaction grain

**One row per `(transaction_id, client_id)` pair.**

The following fields are internally consistent at this grain:

- `transaction_datetime`
- `store_id`
- `purchase_sum`
- `regular_points_received`
- `express_points_received`
- `regular_points_spent`
- `express_points_spent`

The warehouse creates a stable `transaction_key` from the validated composite source business key rather than using `transaction_id` alone.

## Validated transaction-item grain

**One row per `(transaction_id, client_id, product_id)` combination.**

Full-table duplicate count at this grain: **0**.

## Referential integrity

- `purchases.client_id → clients.client_id`: **0 orphan IDs**
- `purchases.product_id → products.product_id`: **0 orphan IDs**

## Columns

### `client_id`

Customer associated with the transaction.

Foreign key: `clients.client_id`.

Part of the validated transaction business key.

### `transaction_id`

Source transaction/basket identifier.

Important:

- repeated across product rows within a transaction
- not globally unique across customer transactions
- 28 values reused across different customers

Do not use `transaction_id` alone as the transaction-fact primary key or as the only join key to transaction items.

### `transaction_datetime`

Purchase transaction timestamp.

Observed range:

- minimum: `2018-11-21 21:02:33`
- maximum: `2019-03-18 23:40:03`

Stable within `(transaction_id, client_id)`.

### `regular_points_received`

Regular loyalty points received/earned.

Transaction-level field repeated across raw product rows.

Observed behavior:

- positive when earned
- average regular points received per transaction: **3.88**

### `express_points_received`

Express/promotional loyalty points received/earned.

Transaction-level field repeated across raw product rows.

Average express points received per transaction: **0.04**.

Across regular and express received points, **98.13%** of transactions earn points.

### `regular_points_spent`

Regular loyalty points spent/redeemed.

Transaction-level field repeated across raw product rows.

Source convention:

- redemption is stored as a **negative** value
- minimum transaction-level value: **-5,066**
- maximum: **0**
- transactions with negative regular-point spend: **495,331**
- transactions with positive regular-point spend: **0**

For analytics, preserve the raw signed field and derive a positive redemption magnitude separately, for example `ABS(regular_points_spent)` when the source value is negative.

Average regular points redeemed when used: **59.31**.

### `express_points_spent`

Express/promotional loyalty points spent/redeemed.

Source convention:

- redemption is stored as a **negative** value
- minimum: **-300**
- maximum: **0**
- transactions with negative express-point spend: **90,469**
- transactions with positive express-point spend: **0**

Average express points redeemed when used: **28.39**.

Across regular and express point types, **6.27%** of transactions contain at least one redemption.

### `purchase_sum`

Transaction monetary amount in the source's currency/unit.

Stable within `(transaction_id, client_id)` and repeated across product rows.

Because it is repeated at raw item grain, summing `purchase_sum` directly across `purchases` would overcount purchase value. The field belongs in `fact_transaction`.

The source does not provide a validated product-level allocation of `purchase_sum`; product/category revenue should not be inferred by attaching the full transaction amount to each product line.

### `store_id`

Anonymized store identifier.

Distinct stores observed: **13,882**.

No descriptive store metadata is available, so `store_id` remains on `fact_transaction` rather than being promoted to an otherwise empty dimension.

### `product_id`

Product identifier.

Foreign key: `products.product_id`.

Part of the validated transaction-item grain.

### `product_quantity`

Quantity of the product purchased.

Item-level measure.

### `trn_sum_from_iss`

Numeric item-level field.

Observed behavior:

- varies within most transactions
- remains at transaction-item grain
- should not be collapsed into the transaction fact

**Semantics unresolved.**

`iss` may refer to issuance, issuer, or another source-system concept. The expansion, unit, and sign convention have not been verified. Keep the source name unchanged and do not treat it as verified revenue or loyalty-points issuance.

### `trn_sum_from_red`

Numeric item-level field.

- missing values: **42,743,212** (~93.35%)
- can vary within a transaction
- does not reliably reconcile with `purchase_sum`

**Semantics unresolved.**

`red` may refer to redemption, but the field has not been established as points, currency, discount, or another unit. It has not been shown to equal the separately validated transaction-level `regular_points_spent` or `express_points_spent` fields.

Keep the source name and do not derive item-level redemption value without authoritative documentation.

## Transaction-level vs item-level structure

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
- `client_id`
- `product_id`
- `product_quantity`
- `trn_sum_from_iss`
- `trn_sum_from_red`

---

# 4. `uplift_train`

## Purpose

Contains treatment assignment and observed outcome information for the development population used in uplift modeling.

## Grain

**One row per training client.**

## Primary key

`client_id`

## Validation

- Rows: **200,039**
- Unique `client_id`: **200,039**
- Duplicate `client_id`: **0**
- Missing values: **0**

## Columns

### `client_id`

Customer identifier.

Foreign key: `clients.client_id`.

### `treatment_flg`

Binary source treatment indicator.

Observed domain: `{0, 1}`.

Counts:

- `0`: **100,058**
- `1`: **99,981**

Proportions:

- control (`0`): **50.0192%**
- treatment (`1`): **49.9808%**

The groups are nearly perfectly balanced in size.

Do not describe the assignment as randomized unless the mechanism is verified from authoritative source documentation.

### `target`

Binary observed outcome.

Observed domain: `{0, 1}`.

Counts:

- `0`: **76,037**
- `1`: **124,002**

Proportions:

- `0`: **38.0111%**
- `1`: **61.9889%**

Treatment × outcome distribution:

| `treatment_flg` | target = 0 | target = 1 | Total |
|---|---:|---:|---:|
| 0 | 39,695 | 60,363 | 100,058 |
| 1 | 36,342 | 63,639 | 99,981 |
| Total | 76,037 | 124,002 | 200,039 |

Observed target rates:

- control: **60.3280%**
- treatment: **63.6511%**
- raw difference: **+3.3231 percentage points**

This difference is descriptive. It is not labeled a causal effect without the assumptions required for causal identification.

---

# 5. `uplift_test`

## Purpose

Contains the client IDs from the original competition scoring/test population. Treatment and target values are not included.

## Grain

**One row per scoring client.**

## Primary key

`client_id`

## Validation

- Rows: **200,123**
- Unique `client_id`: **200,123**
- Duplicate `client_id`: **0**
- Missing `client_id`: **0**

### `client_id`

Customer identifier.

Foreign key: `clients.client_id`.

---

# 6. Verified source relationships

## Clients → uplift split

The complete client population is partitioned exactly between development and scoring populations.

- train/test overlap: **0**
- train + test unique clients: **400,162**
- clients absent from train/test: **0**
- train/test clients absent from `clients`: **0**

## Clients → purchases

`clients.client_id → purchases.client_id`

Orphan purchase client IDs: **0**.

## Products → purchases

`products.product_id → purchases.product_id`

Orphan purchase product IDs: **0**.

---

# 7. Historical timeline and leakage boundary

The analytical flow is conceptually:

```text
customer attributes
      +
historical purchase behavior
      ↓
feature cutoff
      ↓
treatment / no treatment
      ↓
observed target outcome
```

The feature cutoff used by the dbt feature marts and model artifacts is:

`2019-03-19 00:00:00`

Validation found **0** historical transactions at or after the cutoff.

The feature pipeline is intended to prevent post-cutoff/post-treatment information from entering the model inputs.

---

# 8. Data-quality summary

1. Primary source keys are unique for `clients`, `products`, `uplift_train`, and `uplift_test`.
2. Train and test form a complete non-overlapping partition of all **400,162** clients.
3. `first_redeem_date` contains **35,469** missing values.
4. **536** clients have `first_redeem_date < first_issue_date`.
5. `age` contains clearly invalid extremes of **-7,491** and **1,901**.
6. Product missingness is concentrated in `brand_id` (~12.08%), `segment_id` (~3.65%), and `vendor_id` (~0.08%).
7. `is_own_trademark` and `is_alcohol` contain only `{0,1}`.
8. `treatment_flg` and `target` are valid binary fields.
9. The purchase source contains **45,786,568** rows, 0 orphan clients, 0 orphan products, and 0 invalid timestamps.
10. `trn_sum_from_red` is missing in **42,743,212** rows (~93.35%).
11. `transaction_id` is not globally unique; `(transaction_id, client_id)` is the validated transaction grain.
12. `(transaction_id, client_id, product_id)` is the validated item grain with 0 duplicates.
13. `purchase_sum` and loyalty-point fields are transaction-level values repeated across product rows.
14. Loyalty redemption is represented by negative source values in the `*_points_spent` fields.
15. `netto`, `trn_sum_from_iss`, and `trn_sum_from_red` retain unresolved business semantics.

---

# 9. Business profiling summary

## Transaction and customer profile

- Validated customer transactions: **8,045,229**
- Purchasing customers: **400,162**
- Total purchase value: **3,444,393,840.48** in the source's currency/unit
- Average basket value: **428.13**
- Average product lines per transaction: **5.69**
- Average unique products per transaction: **5.69**
- Average units per transaction: **7.10**

All **400,162** clients appear in historical purchase data.

## Customer behavior

- Average transactions per customer: **20.10**
- Median transactions per customer: **15**
- Repeat-customer rate: **98.07%**
- Average customer spend: **8,607.50**
- Median customer spend: **6,111.35**
- Average customer-level average basket value: **496.31**

## Temporal behavior

Historical purchase activity spans **118 calendar dates**.

Daily transaction volume, active customers, purchase value, and average basket value vary materially across the window.

## Product/category behavior

`level_1` contains **3 non-null anonymized categories** plus a null group from the three products with missing `level_1`.

Category analysis uses transaction presence, customers, products, quantity, and line shares rather than assigning the full transaction-level `purchase_sum` to product rows.

## Store behavior

- Distinct stores: **13,882**

Because only an anonymous identifier is available, `store_id` remains on the transaction fact rather than creating a descriptive store dimension.

---

# 10. Core warehouse models

## `dim_customer`

**Grain:** one row per client.

**Rows:** 400,162.

**Primary source:** `clients`.

Purpose:

- customer demographics
- loyalty-program dates
- cleaned/validated attributes
- explicit data-quality indicators

## `dim_product`

**Grain:** one row per product.

**Rows:** 43,038.

**Primary source:** `products`.

Purpose:

- anonymized hierarchy attributes
- segment/brand/vendor identifiers
- private-label and alcohol indicators

## `fact_transaction`

**Grain:** one row per `(transaction_id, client_id)`.

**Rows:** 8,045,229.

Purpose:

- stable `transaction_key`
- transaction timestamp
- customer/store relationship
- purchase amount
- loyalty earning/redemption fields

The fact retains source `transaction_id` and `client_id` for lineage while using the derived key for downstream joins.

## `fact_transaction_item`

**Grain:** one row per `(transaction_id, client_id, product_id)`.

**Rows:** 45,786,568.

Purpose:

- transaction/product relationship
- product quantity
- unresolved item-level source fields `trn_sum_from_iss` and `trn_sum_from_red`

It joins to `fact_transaction` through `transaction_key`, not `transaction_id` alone.

## `fact_treatment_outcome`

**Grain:** one row per uplift-training client.

**Rows:** 200,039.

Purpose:

- treatment indicator
- observed target
- link from the customer dimension into the labeled modeling population

---

# 11. Analytical marts

## `mart_customer_activity`

**Grain:** one row per customer.

**Rows:** 400,162.

Purpose: customer-level activity and transaction behavior for reusable analysis.

## `mart_purchase_daily`

**Grain:** one row per historical calendar date.

**Rows:** 118.

Purpose: daily transaction/customer/purchase monitoring.

## `mart_product_performance`

**Grain:** one row per product.

**Rows:** 43,038.

Purpose: product activity and customer/product usage metrics without misallocating transaction-level purchase value.

## `mart_customer_360`

**Grain:** one row per customer.

**Rows:** 400,162.

Purpose: consolidated customer analytical profile combining demographics, activity, monetary behavior, baskets, loyalty, and product/category behavior.

---

# 12. ML feature marts

## `mart_customer_features`

**Grain:** one row per customer.

**Rows:** 400,162.

**Feature cutoff:** `2019-03-19 00:00:00`.

Purpose: reusable customer feature table used to construct the labeled development and unlabeled scoring populations.

## `mart_uplift_training`

**Grain:** one row per uplift-training customer.

**Rows:** 200,039.

Contains:

- `client_id`
- the model feature contract
- treatment indicator
- target outcome

## `mart_uplift_scoring`

**Grain:** one row per uplift-test/scoring customer.

**Rows:** 200,123.

Contains:

- `client_id`
- the same model feature contract
- no observed treatment/outcome labels

Training/scoring customer overlap: **0**.

---

# 13. Model feature contract

The full-data scoring artifact contains **34 model features**. The canonical feature list is stored in the trusted model artifact and recovered programmatically rather than maintained as a second independent contract.

The feature mart contains the following verified feature groups and fields used in the project.

## Customer profile

### `age`

Validated/cleaned customer age representation used by the model pipeline. Raw invalid age values are not silently rewritten in the source layer.

### `gender`

Customer gender source code (`F`, `M`, or `U`/missing handling according to the model pipeline).

### `customer_tenure_days`

Days between the customer loyalty-program issue date and the feature cutoff.

### `redeemed_before_cutoff_flag`

Indicator that the customer has a recorded redemption date before the feature cutoff.

## Lifetime transaction behavior

### `transaction_count`

Number of validated customer transactions in the historical feature window.

### `active_history_days`

Span of observed customer activity across the historical purchase window.

### `recency_days`

Days from the customer's most recent historical purchase to the feature cutoff.

### `distinct_store_count`

Number of distinct stores visited by the customer.

## Lifetime monetary/basket behavior

### `total_purchase_value`

Sum of transaction-level `purchase_sum` across the customer's validated transactions. It is calculated from the transaction fact, not raw item rows.

### `avg_basket_value`

Mean transaction purchase value for the customer.

### `median_basket_value`

Median transaction purchase value for the customer.

### `max_basket_value`

Maximum transaction purchase value for the customer.

### `basket_value_stddev`

Standard deviation of transaction purchase value for the customer.

## Recent-window behavior

### `transaction_count_30d`

Customer transaction count in the most recent 30-day feature window.

### `transaction_count_prior_30d`

Customer transaction count in the 30-day window immediately preceding the most recent 30 days.

### `transaction_30d_pct`

Share of the customer's lifetime/historical transactions occurring in the most recent 30-day window.

### `purchase_value_30d`

Transaction-level purchase value accumulated in the most recent 30-day window.

### `purchase_value_prior_30d`

Purchase value accumulated in the preceding 30-day window.

### `purchase_value_30d_pct`

Share of the customer's historical purchase value occurring in the most recent 30-day window.

## Loyalty behavior

### `total_regular_points_received`

Customer total of regular points received/earned across validated transactions.

### `total_express_points_received`

Customer total of express/promotional points received/earned.

### `total_regular_points_redeemed`

Positive-magnitude derived measure of regular points redeemed from the negative source spending convention.

### `total_express_points_redeemed`

Positive-magnitude derived measure of express/promotional points redeemed.

### `redemption_transaction_count`

Number of transactions containing at least one regular or express redemption.

### `redemption_transaction_pct`

Share of customer transactions containing a redemption.

## Item/product behavior

### `item_line_count`

Number of historical transaction-product rows associated with the customer.

### `distinct_product_count`

Number of unique products purchased by the customer.

### `total_product_units`

Sum of `product_quantity` across the customer's item rows.

### `distinct_level1_category_count`

Number of distinct non-null `level_1` product categories observed for the customer.

### `own_trademark_item_pct`

Percentage of the customer's item lines whose products have `is_own_trademark = 1`.

### `alcohol_item_pct`

Percentage of the customer's item lines whose products have `is_alcohol = 1`.

## Anonymized `level_1` category shares

The model includes three category-share features derived from the three non-null anonymized `level_1` categories. Each is calculated as:

```text
item lines in that level_1 category
----------------------------------- × 100
all customer item lines
```

Current generated feature names include:

- `category_e344ab2e71_item_pct`
- `category_ec62ce61e3_item_pct`
- `category_c3d3a8e8c6_item_pct`

The hashes are source/anonymized category identifiers; no business category label is inferred.

## Canonical contract rule

If this document and the serialized model artifact ever disagree on feature order or membership, the trusted artifact's `feature_columns` contract and the dbt model used to generate those features must be inspected before scoring. The API enforces the exact serving feature contract rather than accepting arbitrary columns.

---

# 14. Modeling populations and interpretation

## Reference/development population

`mart_uplift_training`: **200,039** customers.

Contains treatment/outcome labels and is used for model development and final full-data refitting.

## Scoring population

`mart_uplift_scoring`: **200,123** customers.

Contains features only. It is used to generate predicted treatment/control probabilities, predicted uplift, and decision-policy outputs.

Because this population has no observed treatment/outcome labels, it cannot directly support post-deployment uplift-performance measurement.

---

# 15. Operational and generated datasets

The following artifacts are part of the engineering system but are **not** historical X5 business datasets.

## Incremental-ingestion demonstration

Location: local generated files + isolated Snowflake `INCREMENTAL_DEMO` objects.

Synthetic event fields:

- `event_id`
- `client_id`
- `event_ts`
- `amount`
- `schema_version`

Purpose:

- demonstrate incremental file arrival
- validate source contracts
- quarantine invalid rows
- preserve source provenance
- demonstrate idempotent business-event promotion

These synthetic records never enter the X5 feature marts or model training data.

## Kafka/Spark streaming demonstration

Synthetic JSON events use the same high-level demonstration fields and are published to Kafka. Spark preserves Kafka partition/offset provenance and writes trusted/quarantine Parquet outputs locally.

Purpose:

- demonstrate event-driven ingestion
- checkpoints
- watermarks
- stateful event-ID deduplication

These events never enter the historical X5 feature marts or model training data.

## Drift-monitoring outputs

Generated under `data/monitoring/`.

Examples:

- feature-drift report
- summary JSON

These are operational monitoring artifacts, not model features or source-of-truth analytical tables.

## Governance outputs

Generated under `data/governance/`.

Examples:

- lineage report
- governance summary

These are audit/provenance artifacts.

## Deployment and MLflow artifacts

Generated model bundles, deployment manifests, local MLflow state, Airflow state, streaming checkpoints, monitoring outputs, and governance outputs are intentionally excluded from Git.

---

# 16. Known unresolved semantics and deferred business definitions

The following source semantics remain intentionally unresolved:

- `products.netto`
- `purchases.trn_sum_from_iss`
- `purchases.trn_sum_from_red`

The project does not silently replace uncertainty with guessed definitions.

Other important boundaries:

- treatment assignment should not be called randomized without authoritative evidence;
- product-level revenue should not be inferred from transaction-level `purchase_sum`;
- negative loyalty-spend values are a source convention and should be converted to positive redemption magnitudes only in explicitly derived fields;
- drift monitoring demonstrates population/prediction stability, not realized post-deployment causal performance.
