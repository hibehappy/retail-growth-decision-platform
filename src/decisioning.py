
# ============================================================
# Retail Growth Experimentation & ML Decisioning Platform
# Treatment decision engine
#
# Purpose:
# Translate predicted customer uplift into contact decisions
# using assumed conversion value, contact cost, and budget.
#
# Important:
# All economic outputs are MODELED SCENARIOS.
# They are not observed revenue or verified causal effects.
#
# Assumptions:
# - One possible contact per customer.
# - Constant value per incremental conversion.
# - Constant cost per contact.
# - No additional eligibility or frequency constraints.
# ============================================================

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 1. Validate the economic assumptions and score inputs
# ------------------------------------------------------------

def validate_inputs(
    scores,
    conversion_value,
    contact_cost,
    budget,
):

    required_columns = {
        "client_id",
        "predicted_uplift",
        "p_treatment",
    }

    missing_columns = (
        required_columns - set(scores.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if scores["client_id"].isna().any():
        raise ValueError("client_id cannot contain nulls.")

    if scores["client_id"].duplicated().any():
        raise ValueError("client_id must be unique.")

    if not np.isfinite(
        scores["predicted_uplift"].to_numpy()
    ).all():
        raise ValueError(
            "predicted_uplift must contain finite values."
        )

    if not scores["predicted_uplift"].between(
        -1,
        1,
    ).all():
        raise ValueError(
            "Predicted uplift must be between -1 and 1."
        )

    if not np.isfinite(
        scores["p_treatment"].to_numpy()
    ).all():
        raise ValueError(
            "p_treatment must contain finite values."
        )

    if not scores["p_treatment"].between(
        0,
        1,
    ).all():
        raise ValueError(
            "p_treatment must be between 0 and 1."
        )

    for name, value in {
        "conversion_value": conversion_value,
        "contact_cost": contact_cost,
        "budget": budget,
    }.items():

        if not np.isfinite(value) or value < 0:
            raise ValueError(
                f"{name} must be finite and nonnegative."
            )


# ------------------------------------------------------------
# 2. Build the budget-constrained contact policy
#
# With constant contact cost and conversion value, each
# customer can be ranked by modeled net value per contact.
#
# Contact customers only when:
#
# predicted_uplift * conversion_value - contact_cost > 0
#
# Then select as many positive-value customers as the
# budget permits.
#
# This simple ranking works under the CONSTANT-COST setup.
# Variable contact costs would require a different
# optimization approach.
# ------------------------------------------------------------

def build_contact_policy(
    scores,
    conversion_value,
    contact_cost,
    budget,
):

    validate_inputs(
        scores,
        conversion_value,
        contact_cost,
        budget,
    )

    candidates = scores[
        [
            "client_id",
            "predicted_uplift",
            "p_treatment",
        ]
    ].copy()

    # Modeled incremental value before paying for contact.
    candidates["modeled_incremental_value"] = (
        candidates["predicted_uplift"]
        * conversion_value
    )

    # Modeled contribution after contact cost.
    candidates["modeled_net_value_per_contact"] = (
        candidates["modeled_incremental_value"]
        - contact_cost
    )

    # Deterministic ordering makes equal-score results
    # reproducible across repeated runs.
    candidates = (
        candidates
        .sort_values(
            [
                "modeled_net_value_per_contact",
                "client_id",
            ],
            ascending=[False, True],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )

    # A zero-cost contact consumes no monetary budget.
    # Otherwise, calculate the maximum affordable contacts.
    if contact_cost == 0:

        max_affordable_contacts = len(candidates)

    else:

        max_affordable_contacts = int(
            np.floor(budget / contact_cost)
        )

    # We do not contact customers whose modeled net value
    # is zero or negative.
    eligible_count = int(
        (
            candidates["modeled_net_value_per_contact"]
            > 0
        ).sum()
    )

    selected_count = min(
        max_affordable_contacts,
        eligible_count,
    )

    candidates["contact"] = False

    candidates.loc[
        candidates.index[:selected_count],
        "contact",
    ] = True

    return candidates


# ------------------------------------------------------------
# 3. Summarize any proposed contact policy
#
# selected_client_ids can come from:
# - optimized targeting
# - random targeting
# - purchase-propensity targeting
# - contacting everyone
#
# These summaries are prediction-based comparisons.
# They do not evaluate observed campaign outcomes.
# ------------------------------------------------------------

def summarize_policy(
    scores,
    selected_client_ids,
    conversion_value,
    contact_cost,
    budget,
    policy_name,
):

    validate_inputs(
        scores,
        conversion_value,
        contact_cost,
        budget,
    )

    selected_ids = set(selected_client_ids)

    unknown_ids = (
        selected_ids
        - set(scores["client_id"])
    )

    if unknown_ids:
        raise ValueError(
            "Policy contains unknown client IDs."
        )

    selected = scores.loc[
        scores["client_id"].isin(selected_ids)
    ]

    contact_count = len(selected)

    # Each predicted uplift is a modeled difference
    # in the probability of a binary target outcome.
    modeled_incremental_conversions = (
        selected["predicted_uplift"].sum()
    )

    modeled_incremental_value = (
        modeled_incremental_conversions
        * conversion_value
    )

    contact_spend = (
        contact_count * contact_cost
    )

    modeled_net_value = (
        modeled_incremental_value
        - contact_spend
    )

    return {
        "policy": policy_name,

        "contacts": contact_count,

        "contact_pct": (
            100.0 * contact_count / len(scores)
        ),

        "modeled_incremental_conversions":
            modeled_incremental_conversions,

        "modeled_incremental_value":
            modeled_incremental_value,

        "contact_spend":
            contact_spend,

        "modeled_net_value":
            modeled_net_value,

        "within_budget": (
            contact_spend <= budget + 1e-8
        ),
    }