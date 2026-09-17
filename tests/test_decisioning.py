
# ============================================================
# Decision engine unit tests
#
# Small synthetic examples with known correct answers.
# No Snowflake connection or ML training required.
# ============================================================

import unittest

import pandas as pd

from src.decisioning import (
    build_contact_policy,
    summarize_policy,
)


class TestDecisioning(unittest.TestCase):

    def setUp(self):

        # Assumed conversion value = 10
        # Assumed contact cost = 0.50
        #
        # Modeled net values:
        #
        # A: 0.20 * 10 - 0.50 =  1.50
        # B: 0.02 * 10 - 0.50 = -0.30
        # C: -0.01 * 10 - 0.50 = -0.60
        # D: 0.10 * 10 - 0.50 =  0.50

        self.scores = pd.DataFrame(
            {
                "client_id": [
                    "A",
                    "B",
                    "C",
                    "D",
                ],
                "predicted_uplift": [
                    0.20,
                    0.02,
                    -0.01,
                    0.10,
                ],
                "p_treatment": [
                    0.70,
                    0.90,
                    0.60,
                    0.75,
                ],
            }
        )


    def test_selects_highest_positive_value(self):

        decisions = build_contact_policy(
            scores=self.scores,
            conversion_value=10.0,
            contact_cost=0.50,
            budget=1.0,
        )

        selected_ids = set(
            decisions.loc[
                decisions["contact"],
                "client_id",
            ]
        )

        self.assertEqual(
            selected_ids,
            {"A", "D"},
        )


    def test_does_not_contact_negative_value_customers(self):

        decisions = build_contact_policy(
            scores=self.scores,
            conversion_value=10.0,
            contact_cost=0.50,
            budget=10.0,
        )

        selected_ids = set(
            decisions.loc[
                decisions["contact"],
                "client_id",
            ]
        )

        self.assertEqual(
            selected_ids,
            {"A", "D"},
        )


    def test_zero_budget_with_positive_cost(self):

        decisions = build_contact_policy(
            scores=self.scores,
            conversion_value=10.0,
            contact_cost=0.50,
            budget=0.0,
        )

        self.assertEqual(
            decisions["contact"].sum(),
            0,
        )


    def test_policy_summary_reconciles(self):

        summary = summarize_policy(
            scores=self.scores,
            selected_client_ids=["A", "D"],
            conversion_value=10.0,
            contact_cost=0.50,
            budget=1.0,
            policy_name="Test policy",
        )

        self.assertEqual(
            summary["contacts"],
            2,
        )

        self.assertAlmostEqual(
            summary["modeled_incremental_conversions"],
            0.30,
        )

        self.assertAlmostEqual(
            summary["modeled_net_value"],
            2.0,
        )

        self.assertTrue(
            summary["within_budget"]
        )


if __name__ == "__main__":
    unittest.main()