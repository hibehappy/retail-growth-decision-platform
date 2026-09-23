# ============================================================
# Retail Growth — Data and model drift monitoring
#
# Purpose:
# Compare a reference population with a current population
# without requiring outcome labels.
#
# Monitoring signals:
#
# - Population Stability Index (PSI)
# - Standardized Mean Difference (SMD)
# - missingness change
# - categorical distribution movement
#
# These functions are reusable outside the notebook so the
# same monitoring logic could later run from Airflow or
# another scheduled workflow.
# ============================================================

from __future__ import annotations

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1. Project monitoring thresholds
#
# These are operational heuristics selected for this project.
# They should NOT be interpreted as universal statistical
# rules.
# ------------------------------------------------------------

PSI_WARNING = 0.10
PSI_CRITICAL = 0.25

MISSINGNESS_WARNING = 0.05
MISSINGNESS_CRITICAL = 0.10

EPSILON = 1e-6


# ------------------------------------------------------------
# 2. Convert counts into stable proportions
#
# PSI contains a logarithm:
#
#     (current - reference) * ln(current / reference)
#
# A category with exactly zero probability would make the
# logarithm undefined.
#
# A very small epsilon prevents division-by-zero while having
# negligible effect on ordinary distributions.
# ------------------------------------------------------------

def _stabilize_proportions(counts):

    counts = np.asarray(
        counts,
        dtype=float,
    )

    counts = counts + EPSILON

    return counts / counts.sum()


# ------------------------------------------------------------
# 3. PSI from two aligned count vectors
# ------------------------------------------------------------

def _psi_from_counts(
    reference_counts,
    current_counts,
):

    reference_pct = (
        _stabilize_proportions(
            reference_counts
        )
    )

    current_pct = (
        _stabilize_proportions(
            current_counts
        )
    )

    contributions = (
        current_pct
        - reference_pct
    ) * np.log(
        current_pct
        / reference_pct
    )

    return float(
        contributions.sum()
    )


# ------------------------------------------------------------
# 4. Numeric PSI
#
# IMPORTANT:
#
# Bin boundaries are learned ONLY from the reference
# population.
#
# We do not create separate quantile bins for each dataset
# because that would make both populations appear artificially
# similar.
#
# Missing values are treated as their own monitoring bucket.
# ------------------------------------------------------------

def numeric_psi(
    reference,
    current,
    bins=10,
):

    reference = pd.to_numeric(
        pd.Series(reference),
        errors="coerce",
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    )

    current = pd.to_numeric(
        pd.Series(current),
        errors="coerce",
    ).replace(
        [np.inf, -np.inf],
        np.nan,
    )

    reference_valid = (
        reference.dropna()
    )

    # If the reference feature is entirely missing, PSI is
    # not meaningful.
    if reference_valid.empty:

        return np.nan

    # --------------------------------------------------------
    # Learn candidate boundaries from reference quantiles.
    # --------------------------------------------------------

    quantiles = np.linspace(
        0,
        1,
        bins + 1,
    )

    boundaries = np.unique(
        reference_valid.quantile(
            quantiles
        ).to_numpy()
    )

    # --------------------------------------------------------
    # Use infinite tails so current observations outside the
    # reference min/max are still counted.
    # --------------------------------------------------------

    internal_boundaries = (
        boundaries[1:-1]
        if len(boundaries) > 2
        else []
    )

    cut_points = np.concatenate(
        (
            [-np.inf],
            internal_boundaries,
            [np.inf],
        )
    )

    reference_bins = pd.cut(
        reference,
        bins=cut_points,
        include_lowest=True,
    )

    current_bins = pd.cut(
        current,
        bins=cut_points,
        include_lowest=True,
    )

    categories = (
        reference_bins.cat.categories
    )

    reference_counts = (
        reference_bins
        .value_counts(sort=False)
        .reindex(
            categories,
            fill_value=0,
        )
        .to_numpy()
    )

    current_counts = (
        current_bins
        .value_counts(sort=False)
        .reindex(
            categories,
            fill_value=0,
        )
        .to_numpy()
    )

    # Add an explicit missing-value bucket.
    reference_counts = np.append(
        reference_counts,
        reference.isna().sum(),
    )

    current_counts = np.append(
        current_counts,
        current.isna().sum(),
    )

    return _psi_from_counts(
        reference_counts,
        current_counts,
    )


# ------------------------------------------------------------
# 5. Categorical PSI
#
# Use the union of categories observed across both datasets.
#
# Missing values are represented explicitly.
# ------------------------------------------------------------

def categorical_psi(
    reference,
    current,
):

    reference = (
        pd.Series(reference)
        .astype("object")
        .where(
            pd.notna(reference),
            "__MISSING__",
        )
        .astype(str)
    )

    current = (
        pd.Series(current)
        .astype("object")
        .where(
            pd.notna(current),
            "__MISSING__",
        )
        .astype(str)
    )

    categories = sorted(
        set(reference.unique())
        | set(current.unique())
    )

    reference_counts = (
        reference
        .value_counts()
        .reindex(
            categories,
            fill_value=0,
        )
        .to_numpy()
    )

    current_counts = (
        current
        .value_counts()
        .reindex(
            categories,
            fill_value=0,
        )
        .to_numpy()
    )

    return _psi_from_counts(
        reference_counts,
        current_counts,
    )


# ------------------------------------------------------------
# 6. Standardized Mean Difference
#
# SMD expresses the difference in population means relative
# to their pooled standard deviation.
#
# Unlike a hypothesis-test p-value, SMD is not inflated simply
# because we have hundreds of thousands of observations.
# ------------------------------------------------------------

def standardized_mean_difference(
    reference,
    current,
):

    reference = pd.to_numeric(
        pd.Series(reference),
        errors="coerce",
    )

    current = pd.to_numeric(
        pd.Series(current),
        errors="coerce",
    )

    reference_mean = reference.mean()
    current_mean = current.mean()

    reference_var = reference.var()
    current_var = current.var()

    pooled_std = np.sqrt(
        (
            reference_var
            + current_var
        )
        / 2
    )

    if pd.isna(pooled_std):

        return np.nan

    if pooled_std == 0:

        if reference_mean == current_mean:
            return 0.0

        return np.inf

    return float(
        (
            current_mean
            - reference_mean
        )
        / pooled_std
    )


# ------------------------------------------------------------
# 7. Monitoring alert classification
#
# PSI and missingness can independently trigger an alert.
#
# CRITICAL overrides WARNING.
# ------------------------------------------------------------

def classify_alert(
    psi,
    missingness_delta,
):

    abs_missingness_delta = abs(
        missingness_delta
    )

    if (
        (
            pd.notna(psi)
            and psi >= PSI_CRITICAL
        )
        or (
            abs_missingness_delta
            >= MISSINGNESS_CRITICAL
        )
    ):

        return "CRITICAL"

    if (
        (
            pd.notna(psi)
            and psi >= PSI_WARNING
        )
        or (
            abs_missingness_delta
            >= MISSINGNESS_WARNING
        )
    ):

        return "WARNING"

    return "OK"


# ------------------------------------------------------------
# 8. Build feature-level drift report
#
# Data types are inferred from the reference dataframe:
#
# numeric dtype      → numeric PSI + SMD
# other dtype        → categorical PSI
# ------------------------------------------------------------

def build_feature_drift_report(
    reference_df,
    current_df,
    feature_columns,
):

    rows = []

    for feature in feature_columns:

        if feature not in reference_df.columns:

            raise ValueError(
                f"Reference population is missing "
                f"feature: {feature}"
            )

        if feature not in current_df.columns:

            raise ValueError(
                f"Current population is missing "
                f"feature: {feature}"
            )

        reference = (
            reference_df[feature]
        )

        current = (
            current_df[feature]
        )

        reference_missing = float(
            reference.isna().mean()
        )

        current_missing = float(
            current.isna().mean()
        )

        missingness_delta = (
            current_missing
            - reference_missing
        )

        if pd.api.types.is_numeric_dtype(
            reference
        ):

            feature_type = "numeric"

            psi = numeric_psi(
                reference,
                current,
            )

            smd = (
                standardized_mean_difference(
                    reference,
                    current,
                )
            )

        else:

            feature_type = "categorical"

            psi = categorical_psi(
                reference,
                current,
            )

            smd = np.nan

        rows.append(
            {
                "feature":
                    feature,

                "feature_type":
                    feature_type,

                "psi":
                    psi,

                "smd":
                    smd,

                "reference_missing_pct":
                    reference_missing * 100,

                "current_missing_pct":
                    current_missing * 100,

                "missingness_delta_pp":
                    missingness_delta * 100,

                "alert":
                    classify_alert(
                        psi,
                        missingness_delta,
                    ),
            }
        )

    report = pd.DataFrame(
        rows
    )

    severity_order = {
        "CRITICAL": 0,
        "WARNING": 1,
        "OK": 2,
    }

    report["_severity"] = (
        report["alert"]
        .map(severity_order)
    )

    report = (
        report
        .sort_values(
            [
                "_severity",
                "psi",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop(
            columns="_severity"
        )
        .reset_index(
            drop=True
        )
    )

    return report


# ------------------------------------------------------------
# 9. Generic one-dimensional distribution report
#
# We can use the same monitoring logic for model predictions,
# not only raw input features.
# ------------------------------------------------------------

def build_numeric_distribution_report(
    reference,
    current,
    name,
):

    reference = pd.Series(
        reference
    )

    current = pd.Series(
        current
    )

    reference_missing = float(
        reference.isna().mean()
    )

    current_missing = float(
        current.isna().mean()
    )

    missingness_delta = (
        current_missing
        - reference_missing
    )

    psi = numeric_psi(
        reference,
        current,
    )

    smd = (
        standardized_mean_difference(
            reference,
            current,
        )
    )

    return {
        "metric": name,
        "reference_mean":
            float(reference.mean()),

        "current_mean":
            float(current.mean()),

        "reference_median":
            float(reference.median()),

        "current_median":
            float(current.median()),

        "psi":
            psi,

        "smd":
            smd,

        "alert":
            classify_alert(
                psi,
                missingness_delta,
            ),
    }