
# ============================================================
# Retail Growth — Warehouse and Feature Refresh DAG
#
# Purpose:
# Coordinate a safe rebuild of the existing Snowflake/dbt
# analytical warehouse and customer feature layer.
#
# This DAG does NOT:
# - Ingest new S3 files
# - Retrain ML models
# - Replace MLflow artifacts
# - Redeploy the API
#
# The DAG is manually triggered until unattended
# authentication and incremental ingestion are configured.
# ============================================================

from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator


# ------------------------------------------------------------
# 1. Resolve repository paths
#
# The DAG lives in:
# orchestration/dags/retail_growth_refresh.py
#
# parents[2] takes us back to the repository root.
#
# Airflow uses its own environment, but invokes the dbt
# executable inside our EXISTING project_env.
# ------------------------------------------------------------

PROJECT_ROOT = (
    Path(__file__).resolve().parents[2]
)

DBT_DIR = (
    PROJECT_ROOT / "dbt"
)

DBT_EXECUTABLE = (
    PROJECT_ROOT
    / "project_env"
    / "bin"
    / "dbt"
)

PYTHON_EXECUTABLE = (
    PROJECT_ROOT
    / "project_env"
    / "bin"
    / "python"
)

VERIFY_SCRIPT = (
    PROJECT_ROOT
    / "scripts"
    / "verify_dbt_build.py"
)


# ------------------------------------------------------------
# 2. Define the DAG
#
# schedule=None:
#   Run only when explicitly triggered.
#
# max_active_runs=1:
#   Prevent two overlapping full warehouse rebuilds.
#
# catchup=False:
#   Do not create historical scheduled runs.
#
# retries=0:
#   Avoid automatically repeating an expensive rebuild
#   until we understand its resource and failure behavior.
# ------------------------------------------------------------

with DAG(
    dag_id="retail_growth_dbt_refresh",
    description=(
        "Validate the fixed X5 snapshot and rebuild "
        "the retail growth warehouse and feature layer."
    ),
    start_date=datetime(
        2026,
        9,
        22,
        tzinfo=timezone.utc,
    ),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={
        "retries": 0,
        "execution_timeout": timedelta(hours=2),
    },
    tags=[
        "retail-growth",
        "snowflake",
        "dbt",
    ],
) as dag:


    # --------------------------------------------------------
    # Task 1: Confirm that dbt can access Snowflake.
    #
    # A failed connection stops the workflow immediately.
    # --------------------------------------------------------

    check_connection = BashOperator(
        task_id="check_snowflake_connection",

        bash_command=(
            "set -euo pipefail; "
            f'"{DBT_EXECUTABLE}" debug '
            f'--project-dir "{DBT_DIR}"'
        ),

        cwd=str(PROJECT_ROOT),
    )


    # --------------------------------------------------------
    # Task 2: Validate the immutable X5 RAW snapshot.
    #
    # The source contract runs BEFORE the costly dbt build.
    # If a source file is missing or partially loaded,
    # downstream transformations do not start.
    # --------------------------------------------------------

    validate_source_snapshot = BashOperator(
        task_id="validate_x5_snapshot",

        bash_command=(
            "set -euo pipefail; "
            f'"{DBT_EXECUTABLE}" test '
            f'--project-dir "{DBT_DIR}" '
            "--select assert_x5_snapshot_counts"
        ),

        cwd=str(PROJECT_ROOT),
    )


    # --------------------------------------------------------
    # Task 3: Run the existing dbt project.
    #
    # dbt determines the model build order internally:
    #
    # staging -> core -> marts -> ML features
    #
    # --exclude prevents rerunning the RAW snapshot test
    # that already passed in the preceding task.
    #
    # All other existing dbt tests remain included.
    # --------------------------------------------------------

    build_warehouse = BashOperator(
        task_id="build_warehouse_and_features",

        bash_command=(
            "set -euo pipefail; "
            f'"{DBT_EXECUTABLE}" build '
            f'--project-dir "{DBT_DIR}" '
            "--exclude assert_x5_snapshot_counts"
        ),

        cwd=str(PROJECT_ROOT),
    )


    # --------------------------------------------------------
    # Task 4: Verify the structured dbt build results.
    #
    # We use project_env's Python because the verification
    # script belongs to our existing project codebase.
    # --------------------------------------------------------

    verify_build = BashOperator(
        task_id="verify_dbt_results",

        bash_command=(
            "set -euo pipefail; "
            f'"{PYTHON_EXECUTABLE}" '
            f'"{VERIFY_SCRIPT}"'
        ),

        cwd=str(PROJECT_ROOT),
    )


    # --------------------------------------------------------
    # 3. Define task dependencies
    #
    # Airflow only runs downstream tasks when their
    # upstream prerequisites succeed.
    # --------------------------------------------------------

    (
        check_connection
        >> validate_source_snapshot
        >> build_warehouse
        >> verify_build
    )