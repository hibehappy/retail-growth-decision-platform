# Retail Growth Decision Platform — Repository Guide

## Purpose

This guide explains where the major parts of the project live, which files are source-controlled versus generated locally, and how the main workflows relate to one another.

The numbered notebooks document the build process. The reusable implementation lives in `src/`, `scripts/`, `dbt/`, `api/`, `orchestration/`, and `streaming/`.

## Repository structure

```text
retail-growth-decision-platform/
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── api/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── data/
│   ├── raw/                  # local raw data, ignored
│   ├── processed/            # local marts/extracts, ignored
│   ├── models/               # trained model artifacts, ignored
│   ├── mlflow/               # local MLflow state, ignored
│   ├── deployment/           # serving bundle, ignored
│   ├── airflow/              # Airflow runtime state/logs, ignored
│   ├── synthetic/            # generated incremental demo data, ignored
│   ├── streaming/            # Spark outputs/checkpoints, ignored
│   ├── monitoring/           # drift outputs, ignored
│   └── governance/           # lineage/governance outputs, ignored
│
├── dbt/
│   ├── models/
│   ├── tests/
│   ├── dbt_project.yml
│   └── target/               # generated dbt artifacts
│
├── docs/
│   ├── causal_assumptions.md
│   ├── data_dictionary.md
│   ├── model_card.md
│   ├── repository_guide.md
│   └── system_architecture.md
│
├── notebooks/
│   └── numbered project notebooks
│
├── orchestration/
│   └── dags/
│       └── retail_growth_refresh.py
│
├── scripts/
│   ├── build_governance_report.py
│   ├── ci_checks.py
│   ├── export_serving_bundle.py
│   ├── final_project_audit.py
│   ├── generate_incremental_demo.py
│   └── verify_dbt_build.py
│
├── sql/
│   └── Snowflake setup, validation, incremental demo, and audit SQL
│
├── src/
│   ├── decisioning.py
│   ├── drift_monitoring.py
│   └── governance.py
│
├── streaming/
│   ├── docker-compose.yml
│   ├── events.py
│   ├── produce_events.py
│   ├── requirements.txt
│   └── spark_pipeline.py
│
├── tests/
│   └── Python unit tests
│
├── .gitignore
├── README.md
└── requirements.txt
```

The exact notebook filenames may evolve, but their numeric order should remain the primary navigation mechanism.

## What belongs in Git

Version-controlled files should describe **how the system works**, not contain local/private runtime state.

Commit:

- Python source code
- SQL
- dbt models and tests
- notebooks
- documentation
- Dockerfiles
- GitHub Actions workflows
- Airflow DAG definitions
- Kafka/Spark code and local compose configuration
- deterministic generators and validation scripts
- unit tests

Do not commit:

- credentials or `.env`
- virtual environments
- raw/private extracts
- processed Parquet caches
- trained model binaries
- local MLflow database/artifacts
- deployment bundles
- Airflow logs/database
- synthetic generated CSVs
- Spark outputs/checkpoints
- monitoring reports
- governance reports

Recommended ignored paths include:

```text
.env
project_env/
airflow_env/
streaming_env/
data/raw/
data/processed/
data/models/
data/mlflow/
data/deployment/
data/airflow/
data/synthetic/
data/streaming/
data/monitoring/
data/governance/
```

Do not globally ignore all CSV files because SQL/dbt/project fixtures or other intentionally versioned CSV assets may be useful later.

## Documentation map

### `README.md`

The fastest overview. It explains the problem, architecture, major quantitative results, reliability controls, limitations, and where to go next.

### `docs/system_architecture.md`

The canonical architecture document. It explains the historical data path, model/decision path, serving layer, reliability components, streaming/incremental boundaries, drift monitoring, and governance.

### `docs/data_dictionary.md`

The canonical data reference. Use it for source-field semantics, grains, keys, row counts, warehouse models, marts, feature groups, and known quality issues.

### `docs/model_card.md`

Use it for intended model use, evaluation results, causal limitations, economic assumptions, monitoring, and known limitations.

### `docs/causal_assumptions.md`

Use it when evaluating whether modeled uplift can be interpreted causally. The project does not assume verified randomization simply because observed treatment/control groups are balanced.

## Notebook map

The notebooks tell the development story. At a high level they cover:

```text
source audit + warehouse design
        ↓
Snowflake / dbt transformation
        ↓
feature engineering
        ↓
uplift baseline + model evaluation
        ↓
economic decisioning
        ↓
MLflow reproducibility
        ↓
FastAPI + Docker serving
        ↓
Airflow orchestration
        ↓
incremental ingestion + contracts
        ↓
GitHub Actions CI
        ↓
Kafka + Spark streaming
        ↓
data/model drift monitoring
        ↓
governance + lineage + cost controls
        ↓
final end-to-end platform evaluation
```

Use notebook numbers when referring to implementation milestones; avoid a second independent numbering scheme.

## Core reusable modules

### `src/decisioning.py`

Contains the reusable economic contact-policy logic.

Responsibilities include:

- validating scoring inputs
- converting predicted uplift into modeled incremental/net value
- applying positivity and budget constraints
- returning selected contacts
- summarizing modeled policy economics

Notebook code should call this module rather than reimplementing policy logic.

### `src/drift_monitoring.py`

Contains reusable monitoring logic for:

- numeric PSI
- categorical PSI
- standardized mean difference
- missingness deltas
- alert classification
- feature-level drift reports
- prediction-distribution reports

The thresholds are project-level operational heuristics, not universal statistical rules.

### `src/governance.py`

Contains reusable governance utilities for:

- SHA-256 artifact fingerprinting
- loading dbt manifest JSON
- locating dbt model nodes
- recursively tracing upstream dependencies
- producing tabular lineage reports

## dbt project

The dbt project is the transformation source of truth.

Important model layers:

```text
RAW source declarations
      ↓
staging/core transformations
      ↓
dim_customer / dim_product
fact_transaction / fact_transaction_item
fact_treatment_outcome
      ↓
analytical marts
      ↓
mart_customer_features
      ↓
mart_uplift_training / mart_uplift_scoring
```

Important final row counts:

- `dim_customer`: 400,162
- `dim_product`: 43,038
- `fact_transaction`: 8,045,229
- `fact_transaction_item`: 45,786,568
- `fact_treatment_outcome`: 200,039
- `mart_customer_features`: 400,162
- `mart_uplift_training`: 200,039
- `mart_uplift_scoring`: 200,123

The strict X5 snapshot contract verifies raw source counts for the fixed benchmark files.

## Snowflake SQL

The `sql/` directory is for setup, manual investigation, and operational/audit queries that should remain readable outside dbt.

dbt owns transformation DAG logic. SQL scripts should not duplicate dbt transformations merely to create another copy of the same business logic.

The distinction is:

- `dbt/models/`: production-style transformation logic
- `dbt/tests/`: dbt invariant/contract tests
- `sql/`: setup, exploration, validation, and operational audits

## Airflow workflow

DAG: `retail_growth_dbt_refresh`.

Current order:

```text
check_snowflake_connection
        ↓
validate_x5_snapshot
        ↓
build_warehouse_and_features
        ↓
verify_dbt_results
```

The DAG is manually triggered because the X5 source is a fixed historical snapshot and local Snowflake authentication may be interactive.

Airflow orchestrates existing dbt commands; it does not duplicate dbt's transformation logic.

## CI workflow

GitHub Actions runs on pushes/pull requests to validate the repository on a clean environment.

Quality gates include:

- repository hygiene
- Python compilation/syntax
- unit tests
- dbt static parse using a dummy non-production profile
- Docker build

CI deliberately does not connect to Snowflake or AWS and does not retrain or deploy the model.

## Model and deployment flow

```text
Notebook development/evaluation
        ↓
full-data logistic T-learner
        ↓
trusted local joblib artifact
        ↓
MLflow model references
        ↓
export_serving_bundle.py
        ↓
model_bundle.joblib + deployment_manifest.json
        ↓
FastAPI
        ↓
Docker
```

The deployment bundle is generated locally and excluded from Git.

The API should always reuse the shared decision-engine logic rather than maintaining a second copy of the economic policy implementation.

## Incremental-ingestion workflow

The incremental demo uses deterministic synthetic CSV batches and isolated Snowflake objects.

Its purpose is to demonstrate:

- new-file loading
- schema/header contract checks
- raw-value preservation
- parsing/validation
- quarantine
- duplicate protection
- idempotency

The synthetic data must never be unioned into the historical X5 marts.

## Streaming workflow

The streaming demo uses a local Kafka broker and Spark Structured Streaming.

```text
synthetic producer
      ↓
Kafka topic
      ↓
Spark Structured Streaming
      ↓
parse + validate
      ↓
trusted / quarantine Parquet
```

The demo preserves Kafka partition/offset provenance and uses checkpoints and a watermark for stateful deduplication.

Generated streaming outputs and checkpoints live under `data/streaming/` and are not committed.

## Drift-monitoring workflow

The reference population is the model-development feature population, and the current demonstration population is the separate X5 scoring feature population.

The comparison demonstrates the monitoring framework; it should not be described as genuine chronological production drift because these are benchmark partitions rather than production snapshots separated in time.

A controlled synthetic shift is used to verify that the detector raises alerts when known features move materially.

## Governance workflow

`dbt/target/manifest.json` is the machine-readable transformation-lineage source.

Primary targets:

- `mart_customer_features`
- `mart_uplift_training`
- `mart_uplift_scoring`

`build_governance_report.py` combines lineage information with model metadata and the trusted artifact checksum.

Generated governance outputs belong in `data/governance/` and should not be committed.

## Common commands

### Activate the main project environment

```bash
source project_env/bin/activate
```

### Run the full Python test suite

```bash
python -m unittest discover \
  -s tests \
  -p "test_*.py"
```

### Run local CI-equivalent checks

```bash
python scripts/ci_checks.py
```

### Build dbt project

Run from the repository root:

```bash
dbt build --project-dir dbt
```

### Verify dbt build artifact

```bash
python scripts/verify_dbt_build.py
```

### Build governance report

```bash
python scripts/build_governance_report.py
```

### Run final structural audit

```bash
python scripts/final_project_audit.py
```

### Build API image

```bash
docker build \
  -f api/Dockerfile \
  -t retail-growth-api .
```

### Start local Kafka

```bash
docker compose \
  -f streaming/docker-compose.yml \
  up -d
```

## Reviewer path

For a fast technical review:

1. Read `README.md`.
2. Read `docs/system_architecture.md`.
3. Read `docs/model_card.md`.
4. Inspect `src/decisioning.py` and `src/drift_monitoring.py`.
5. Inspect the dbt feature marts and tests.
6. Inspect `.github/workflows/ci.yml` and the Airflow DAG.
7. Use the numbered notebooks for detailed experiment history and outputs.

The repository should be understandable without requiring a reviewer to execute every notebook.
