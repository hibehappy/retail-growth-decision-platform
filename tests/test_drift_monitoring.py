# ============================================================
# Data/model drift monitoring unit tests
#
# These tests use tiny deterministic populations.
# No Snowflake or model artifact is required.
# ============================================================

import unittest

import numpy as np
import pandas as pd

from src.drift_monitoring import (
    build_feature_drift_report,
    categorical_psi,
    numeric_psi,
)


class TestDriftMonitoring(unittest.TestCase):

    def test_identical_numeric_population_has_near_zero_psi(
        self,
    ):

        population = pd.Series(
            np.arange(
                1,
                101,
            )
        )

        psi = numeric_psi(
            population,
            population.copy(),
        )

        self.assertAlmostEqual(
            psi,
            0.0,
            places=8,
        )


    def test_shifted_numeric_population_has_positive_psi(
        self,
    ):

        reference = pd.Series(
            np.arange(
                1,
                101,
            )
        )

        current = reference + 100

        psi = numeric_psi(
            reference,
            current,
        )

        self.assertGreater(
            psi,
            0.25,
        )


    def test_categorical_shift_is_detected(
        self,
    ):

        reference = pd.Series(
            ["A"] * 90
            + ["B"] * 10
        )

        current = pd.Series(
            ["A"] * 10
            + ["B"] * 90
        )

        psi = categorical_psi(
            reference,
            current,
        )

        self.assertGreater(
            psi,
            0.25,
        )


    def test_severe_shift_creates_critical_alert(
        self,
    ):

        reference = pd.DataFrame(
            {
                "feature":
                    np.arange(
                        1,
                        101,
                    )
            }
        )

        current = pd.DataFrame(
            {
                "feature":
                    np.arange(
                        101,
                        201,
                    )
            }
        )

        report = (
            build_feature_drift_report(
                reference,
                current,
                ["feature"],
            )
        )

        self.assertEqual(
            report.loc[
                0,
                "alert",
            ],
            "CRITICAL",
        )


if __name__ == "__main__":
    unittest.main()