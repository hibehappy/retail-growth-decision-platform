
# ============================================================
# Unit tests for dbt execution-result verification
#
# These tests use synthetic results.
# They do not connect to Snowflake or rebuild the warehouse.
# ============================================================

import unittest

from scripts.verify_dbt_build import (
    validate_run_results,
    REQUIRED_MODELS,
)


class TestPipelineChecks(unittest.TestCase):

    def make_success_payload(self):

        return {
            "results": [
                {
                    "unique_id": model_id,
                    "status": "success",
                }
                for model_id in sorted(REQUIRED_MODELS)
            ] + [
                {
                    "unique_id": "test.retail_growth.example",
                    "status": "pass",
                }
            ]
        }


    def test_accepts_successful_build(self):

        summary = validate_run_results(
            self.make_success_payload()
        )

        self.assertEqual(
            summary["required_models_verified"],
            3,
        )


    def test_rejects_failed_resource(self):

        payload = self.make_success_payload()

        payload["results"][-1]["status"] = "fail"

        with self.assertRaises(ValueError):

            validate_run_results(
                payload
            )


    def test_rejects_missing_required_model(self):

        payload = self.make_success_payload()

        payload["results"] = [
            result
            for result in payload["results"]
            if result["unique_id"]
            != "model.retail_growth.mart_uplift_scoring"
        ]

        with self.assertRaises(ValueError):

            validate_run_results(
                payload
            )


if __name__ == "__main__":
    unittest.main()