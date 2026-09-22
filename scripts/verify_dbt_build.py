
# ============================================================
# Retail Growth — dbt build verification
#
# Purpose:
# Inspect dbt's structured execution results and confirm
# that the expected modeling marts were successfully built.
#
# This script does NOT run SQL, retrain a model, or connect
# directly to Snowflake.
#
# Run:
# python scripts/verify_dbt_build.py
# ============================================================

from collections import Counter
from pathlib import Path
import json
import sys


# ------------------------------------------------------------
# 1. Identify the models that must exist in the build.
#
# These are our customer feature and uplift populations.
# ------------------------------------------------------------

REQUIRED_MODELS = {
    "model.retail_growth.mart_customer_features",
    "model.retail_growth.mart_uplift_training",
    "model.retail_growth.mart_uplift_scoring",
}

SUCCESS_STATUSES = {
    "success",
    "pass",
}


# ------------------------------------------------------------
# 2. Reusable validation function
#
# Keep this independent of file paths so it can be tested
# using small synthetic dbt results.
# ------------------------------------------------------------

def validate_run_results(payload):

    results = payload.get("results", [])

    if not results:
        raise ValueError(
            "dbt run_results.json contains no executed resources."
        )

    unsuccessful = [
        result
        for result in results
        if result.get("status") not in SUCCESS_STATUSES
    ]

    if unsuccessful:

        details = [
            {
                "unique_id":
                    result.get("unique_id"),

                "status":
                    result.get("status"),
            }
            for result in unsuccessful
        ]

        raise ValueError(
            f"Unsuccessful dbt resources: {details}"
        )


    # --------------------------------------------------------
    # Verify that the build actually included our three
    # required customer-level modeling marts.
    #
    # This prevents a successful but unrelated dbt command
    # from being mistaken for a full warehouse refresh.
    # --------------------------------------------------------

    built_models = {
        result["unique_id"]
        for result in results
        if result.get("unique_id", "").startswith("model.")
        and result.get("status") == "success"
    }

    missing_models = (
        REQUIRED_MODELS - built_models
    )

    if missing_models:
        raise ValueError(
            f"Required models missing from build: {missing_models}"
        )


    # --------------------------------------------------------
    # Return a small execution summary for logs and
    # the inspection notebook.
    # --------------------------------------------------------

    statuses = Counter(
        result["status"]
        for result in results
    )

    return {
        "total_resources": len(results),
        "statuses": dict(statuses),
        "required_models_verified":
            len(REQUIRED_MODELS),
    }


# ------------------------------------------------------------
# 3. Command-line entry point
# ------------------------------------------------------------

if __name__ == "__main__":

    PROJECT_ROOT = (
        Path(__file__).resolve().parents[1]
    )

    RESULTS_PATH = (
        PROJECT_ROOT
        / "dbt"
        / "target"
        / "run_results.json"
    )

    if not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"dbt results not found: {RESULTS_PATH}"
        )

    payload = json.loads(
        RESULTS_PATH.read_text(
            encoding="utf-8"
        )
    )

    summary = validate_run_results(
        payload
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    print("PASS: dbt build verification completed.")