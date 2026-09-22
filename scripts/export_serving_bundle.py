
# ============================================================
# Retail Growth Experimentation & ML Decisioning Platform
# Export MLflow models for API serving
#
# Purpose:
# - Load the exact models recorded in Notebook 06.
# - Preserve their MLflow provenance and feature contract.
# - Verify predictions against Notebook 05.
# - Create a portable serving bundle.
#
# This script does NOT retrain either model.
#
# Run from the repository root:
# python scripts/export_serving_bundle.py
# ============================================================

from pathlib import Path
import hashlib
import json

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1. Resolve project paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRACKING_DB = (
    PROJECT_ROOT
    / "data"
    / "mlflow"
    / "mlflow.db"
)

MLFLOW_MANIFEST_PATH = (
    PROJECT_ROOT
    / "data"
    / "models"
    / "mlflow_model_manifest.json"
)

ORIGINAL_BUNDLE_PATH = (
    PROJECT_ROOT
    / "data"
    / "models"
    / "logistic_t_learner_full.joblib"
)

SCORING_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "mart_uplift_scoring.parquet"
)

PREDICTION_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "uplift_scoring_predictions.parquet"
)

DEPLOYMENT_DIR = (
    PROJECT_ROOT
    / "data"
    / "deployment"
)

BUNDLE_PATH = (
    DEPLOYMENT_DIR
    / "model_bundle.joblib"
)

DEPLOYMENT_MANIFEST_PATH = (
    DEPLOYMENT_DIR
    / "deployment_manifest.json"
)

SAMPLE_REQUEST_PATH = (
    DEPLOYMENT_DIR
    / "sample_request.json"
)


# ------------------------------------------------------------
# 2. Verify that the previous notebook's artifacts exist
#
# We fail explicitly rather than silently training a
# replacement model or choosing a different MLflow run.
# ------------------------------------------------------------

required_files = [
    TRACKING_DB,
    MLFLOW_MANIFEST_PATH,
    ORIGINAL_BUNDLE_PATH,
    SCORING_PATH,
    PREDICTION_PATH,
]

missing_files = [
    path for path in required_files
    if not path.exists()
]

if missing_files:
    raise FileNotFoundError(
        f"Missing required artifacts: {missing_files}"
    )


# ------------------------------------------------------------
# 3. Load the exact MLflow model references
#
# Do not select "latest" or search for a model by name.
# The manifest identifies the specific recorded artifacts.
# ------------------------------------------------------------

mlflow.set_tracking_uri(
    f"sqlite:///{TRACKING_DB.as_posix()}"
)

mlflow_manifest = json.loads(
    MLFLOW_MANIFEST_PATH.read_text(
        encoding="utf-8"
    )
)

original_bundle = joblib.load(
    ORIGINAL_BUNDLE_PATH
)

treatment_model = mlflow.sklearn.load_model(
    mlflow_manifest["treatment_model_uri"]
)

control_model = mlflow.sklearn.load_model(
    mlflow_manifest["control_model_uri"]
)

feature_columns = list(
    original_bundle["feature_columns"]
)


# ------------------------------------------------------------
# 4. Verify the loaded MLflow models against saved predictions
#
# Use the SAME customers and feature-column order.
#
# This checks that we're exporting the intended model
# artifacts, not merely two models with similar names.
# ------------------------------------------------------------

scoring_df = pd.read_parquet(
    SCORING_PATH
)

saved_predictions = pd.read_parquet(
    PREDICTION_PATH
)

scoring_df.columns = scoring_df.columns.str.lower()
saved_predictions.columns = (
    saved_predictions.columns.str.lower()
)

assert scoring_df["client_id"].reset_index(
    drop=True
).equals(
    saved_predictions["client_id"].reset_index(
        drop=True
    )
)

assert set(feature_columns).issubset(
    scoring_df.columns
)

X_sample = scoring_df[
    feature_columns
].head(100)

treatment_probability = (
    treatment_model.predict_proba(
        X_sample
    )[:, 1]
)

control_probability = (
    control_model.predict_proba(
        X_sample
    )[:, 1]
)

np.testing.assert_allclose(
    treatment_probability,
    saved_predictions["p_treatment"].iloc[:100],
    rtol=1e-10,
    atol=1e-10,
)

np.testing.assert_allclose(
    control_probability,
    saved_predictions["p_control"].iloc[:100],
    rtol=1e-10,
    atol=1e-10,
)


# ------------------------------------------------------------
# 5. Export the serving bundle
#
# The API needs the two models, ordered feature schema,
# and provenance—not the entire MLflow tracking database.
# ------------------------------------------------------------

DEPLOYMENT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

serving_bundle = {
    "treatment_model": treatment_model,
    "control_model": control_model,
    "feature_columns": feature_columns,
    "feature_cutoff":
        original_bundle["feature_cutoff"],
    "mlflow_run_id":
        mlflow_manifest["mlflow_run_id"],
    "treatment_model_uri":
        mlflow_manifest["treatment_model_uri"],
    "control_model_uri":
        mlflow_manifest["control_model_uri"],
}

joblib.dump(
    serving_bundle,
    BUNDLE_PATH,
)


# ------------------------------------------------------------
# 6. Fingerprint the exported artifact
#
# The checksum detects accidental file changes.
# It is NOT a substitute for authenticating the artifact's
# source or protecting the deployment directory.
# ------------------------------------------------------------

digest = hashlib.sha256()

with BUNDLE_PATH.open("rb") as file:
    for chunk in iter(
        lambda: file.read(1024 * 1024),
        b"",
    ):
        digest.update(chunk)

deployment_manifest = {
    "model_family": "logistic_t_learner",
    "mlflow_run_id":
        mlflow_manifest["mlflow_run_id"],
    "treatment_model_uri":
        mlflow_manifest["treatment_model_uri"],
    "control_model_uri":
        mlflow_manifest["control_model_uri"],
    "feature_count": len(feature_columns),
    "feature_cutoff":
        original_bundle["feature_cutoff"],
    "model_sha256": digest.hexdigest(),
}

DEPLOYMENT_MANIFEST_PATH.write_text(
    json.dumps(
        deployment_manifest,
        indent=2,
    ),
    encoding="utf-8",
)


# ------------------------------------------------------------
# 7. Generate one valid example request for API testing
#
# Convert pandas/numpy scalar values into ordinary Python
# values and represent missing values as JSON null.
#
# This example is for LOCAL testing only; the deployment
# directory must remain excluded from Git.
# ------------------------------------------------------------

example = scoring_df.iloc[0]

example_features = {}

for column in feature_columns:

    value = example[column]

    if pd.isna(value):
        example_features[column] = None

    elif isinstance(value, np.generic):
        example_features[column] = value.item()

    else:
        example_features[column] = value


sample_request = {
    "customers": [
        {
            "client_id": str(example["client_id"]),
            "features": example_features,
        }
    ]
}

SAMPLE_REQUEST_PATH.write_text(
    json.dumps(
        sample_request,
        indent=2,
        allow_nan=False,
    ),
    encoding="utf-8",
)


print("PASS: MLflow models loaded.")
print("PASS: Predictions match Notebook 05.")
print(f"Feature count: {len(feature_columns)}")
print(f"MLflow run: {mlflow_manifest['mlflow_run_id']}")
print(f"Serving bundle: {BUNDLE_PATH}")
print(f"Sample request: {SAMPLE_REQUEST_PATH}")