
# ============================================================
# FastAPI unit tests
#
# These tests use a temporary toy serving bundle.
# No real customer data, MLflow server, or Snowflake required.
# ============================================================

import hashlib
import json
import tempfile
import unittest

from pathlib import Path

import joblib
import numpy as np

from fastapi.testclient import TestClient

from api.app import create_app


# ------------------------------------------------------------
# A deterministic model with the same predict_proba
# interface as the real sklearn pipelines.
# ------------------------------------------------------------

class ConstantOutcomeModel:

    def __init__(self, probability):

        self.probability = probability

    def predict_proba(self, X):

        n = len(X)

        return np.column_stack(
            [
                np.full(
                    n,
                    1 - self.probability,
                ),
                np.full(
                    n,
                    self.probability,
                ),
            ]
        )


class TestAPI(unittest.TestCase):

    def setUp(self):

        self.temp_dir = tempfile.TemporaryDirectory()

        directory = Path(
            self.temp_dir.name
        )

        bundle_path = (
            directory
            / "model_bundle.joblib"
        )

        bundle = {
            "treatment_model":
                ConstantOutcomeModel(0.70),

            "control_model":
                ConstantOutcomeModel(0.50),

            "feature_columns": [
                "age",
                "gender",
            ],

            "feature_cutoff":
                "2019-03-19 00:00:00",

            "mlflow_run_id":
                "test-run-001",
        }

        joblib.dump(
            bundle,
            bundle_path,
        )

        digest = hashlib.sha256(
            bundle_path.read_bytes()
        ).hexdigest()

        manifest = {
            "mlflow_run_id":
                "test-run-001",

            "model_sha256":
                digest,
        }

        (
            directory
            / "deployment_manifest.json"
        ).write_text(
            json.dumps(manifest),
            encoding="utf-8",
        )

        self.app = create_app(
            bundle_path=bundle_path
        )

        self.client_context = TestClient(
            self.app
        )

        # Enter the context to execute FastAPI's
        # lifespan startup and load the toy model.
        self.client = (
            self.client_context.__enter__()
        )

        self.customer = {
            "client_id": "A",
            "features": {
                "age": 40,
                "gender": "F",
            },
        }


    def tearDown(self):

        self.client_context.__exit__(
            None,
            None,
            None,
        )

        self.temp_dir.cleanup()


    def test_health_and_model_version(self):

        response = self.client.get(
            "/health"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["mlflow_run_id"],
            "test-run-001",
        )


    def test_uplift_scoring(self):

        response = self.client.post(
            "/score",
            json={
                "customers": [
                    self.customer
                ]
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        prediction = response.json()[
            "predictions"
        ][0]

        self.assertAlmostEqual(
            prediction["p_treatment"],
            0.70,
        )

        self.assertAlmostEqual(
            prediction["p_control"],
            0.50,
        )

        self.assertAlmostEqual(
            prediction["predicted_uplift"],
            0.20,
        )


    def test_rejects_missing_feature(self):

        response = self.client.post(
            "/score",
            json={
                "customers": [
                    {
                        "client_id": "A",
                        "features": {
                            "age": 40,
                        },
                    }
                ]
            },
        )

        self.assertEqual(
            response.status_code,
            422,
        )


    def test_decision_respects_budget(self):

        response = self.client.post(
            "/decide",
            json={
                "customers": [
                    self.customer
                ],
                "conversion_value": 10.0,
                "contact_cost": 0.50,
                "budget": 0.0,
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        result = response.json()

        self.assertEqual(
            result["summary"]["contacts"],
            0,
        )

        self.assertTrue(
            result["summary"]["within_budget"]
        )


if __name__ == "__main__":
    unittest.main()