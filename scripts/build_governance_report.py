# ============================================================
# Retail Growth — Build governance report
#
# Produces a machine-readable summary of:
#
# - dbt lineage
# - model artifact integrity
# - feature contract
# - model provenance
#
# Generated output is stored under data/governance and is
# intentionally excluded from Git.
# ============================================================

import json
from pathlib import Path
import sys

import joblib


PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
)

sys.path.insert(
    0,
    str(PROJECT_ROOT),
)


from src.governance import (
    build_lineage_report,
    load_json,
    sha256_file,
)


DBT_MANIFEST = (
    PROJECT_ROOT
    / "dbt"
    / "target"
    / "manifest.json"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "data"
    / "models"
    / "logistic_t_learner_full.joblib"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "governance"
)


TARGET_MODELS = [
    "mart_customer_features",
    "mart_uplift_training",
    "mart_uplift_scoring",
]


def main():

    if not DBT_MANIFEST.exists():

        raise FileNotFoundError(
            "dbt manifest.json was not found. "
            "Run dbt parse or dbt build first."
        )

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            "Trusted model artifact "
            "was not found."
        )

    manifest = load_json(
        DBT_MANIFEST
    )

    lineage = build_lineage_report(
        manifest,
        TARGET_MODELS,
    )

    # --------------------------------------------------------
    # Load only the trusted model created by this project.
    # --------------------------------------------------------

    model_bundle = joblib.load(
        MODEL_PATH
    )

    feature_columns = list(
        model_bundle[
            "feature_columns"
        ]
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    lineage.to_parquet(
        OUTPUT_DIR
        / "lineage_report.parquet",
        index=False,
    )

    summary = {

        "model_artifact":
            str(
                MODEL_PATH.relative_to(
                    PROJECT_ROOT
                )
            ),

        "model_sha256":
            sha256_file(
                MODEL_PATH
            ),

        "model_family":
            model_bundle.get(
                "model_family"
            ),

        "feature_cutoff":
            str(
                model_bundle.get(
                    "feature_cutoff"
                )
            ),

        "feature_count":
            len(
                feature_columns
            ),

        "feature_columns":
            feature_columns,

        "lineage_targets":
            TARGET_MODELS,

        "lineage_resources":
            int(
                len(lineage)
            ),
    }

    (
        OUTPUT_DIR
        / "governance_summary.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()