
# ============================================================
# Retail Growth Experimentation & ML Decisioning Platform
# FastAPI model-serving application
#
# Purpose:
# - Serve a specific exported MLflow model version.
# - Validate incoming customer features.
# - Return uplift predictions.
# - Apply the existing budget-constrained decision engine.
#
# The API does not connect to Snowflake or retrain models.
# ============================================================

from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import json
import os

import joblib
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from src.decisioning import (
    build_contact_policy,
    summarize_policy,
)


# ------------------------------------------------------------
# 1. Request schemas
#
# Each customer must provide:
# - a unique client ID
# - exactly the feature columns expected by the model
#
# Limit request size so this local demonstration cannot
# accidentally attempt to score millions of rows at once.
# ------------------------------------------------------------

class CustomerInput(BaseModel):

    client_id: str = Field(
        min_length=1,
    )

    features: dict[
        str,
        float | int | str | None,
    ]


class ScoreRequest(BaseModel):

    customers: list[CustomerInput] = Field(
        min_length=1,
        max_length=1000,
    )


class DecisionRequest(ScoreRequest):

    conversion_value: float = Field(
        ge=0,
        allow_inf_nan=False,
    )

    contact_cost: float = Field(
        ge=0,
        allow_inf_nan=False,
    )

    budget: float = Field(
        ge=0,
        allow_inf_nan=False,
    )


# ------------------------------------------------------------
# 2. Load and verify the serving artifact
#
# Only load trusted, locally exported model files.
# joblib deserialization can execute Python code.
# ------------------------------------------------------------

def load_bundle(bundle_path):

    bundle_path = Path(bundle_path)

    manifest_path = (
        bundle_path.parent
        / "deployment_manifest.json"
    )

    if not bundle_path.exists():
        raise FileNotFoundError(
            f"Model bundle not found: {bundle_path}"
        )

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"Deployment manifest not found: {manifest_path}"
        )

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8"
        )
    )

    digest = hashlib.sha256()

    with bundle_path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    if digest.hexdigest() != manifest["model_sha256"]:
        raise ValueError(
            "Serving bundle checksum does not match manifest."
        )

    bundle = joblib.load(
        bundle_path
    )

    if (
        bundle["mlflow_run_id"]
        != manifest["mlflow_run_id"]
    ):
        raise ValueError(
            "Model provenance does not match manifest."
        )

    return bundle


# ------------------------------------------------------------
# 3. Create the app
#
# The factory also lets unit tests load a temporary toy
# model instead of requiring the real 200k-customer artifact.
# ------------------------------------------------------------

def create_app(bundle_path=None):

    if bundle_path is None:

        bundle_path = os.getenv(
            "MODEL_BUNDLE_PATH",
            "data/deployment/model_bundle.joblib",
        )

    @asynccontextmanager
    async def lifespan(app: FastAPI):

        app.state.model_bundle = load_bundle(
            bundle_path
        )

        yield

        app.state.model_bundle = None


    app = FastAPI(
        title="Retail Growth Decisioning API",
        version="0.1.0",
        lifespan=lifespan,
    )


    # --------------------------------------------------------
    # Convert API customer records into the exact feature
    # matrix expected by the fitted sklearn pipelines.
    #
    # Never trust the order of fields in incoming JSON.
    # Use the model's recorded feature_columns instead.
    # --------------------------------------------------------

    def prepare_customers(customers, bundle):

        feature_columns = bundle[
            "feature_columns"
        ]

        client_ids = [
            customer.client_id
            for customer in customers
        ]

        if len(client_ids) != len(set(client_ids)):
            raise HTTPException(
                status_code=422,
                detail="client_id must be unique within a request.",
            )

        expected = set(feature_columns)

        rows = []

        for customer in customers:

            provided = set(
                customer.features
            )

            if provided != expected:

                raise HTTPException(
                    status_code=422,
                    detail={
                        "client_id": customer.client_id,
                        "missing_features":
                            sorted(expected - provided),
                        "unexpected_features":
                            sorted(provided - expected),
                    },
                )

            rows.append(
                {
                    column: customer.features[column]
                    for column in feature_columns
                }
            )

        X = pd.DataFrame(
            rows,
            columns=feature_columns,
        )


        # ----------------------------------------------------
        # The current feature schema contains numeric
        # predictors and one categorical predictor: gender.
        #
        # Missing values remain NaN so the fitted
        # preprocessing pipelines can impute them.
        # ----------------------------------------------------

        numeric_columns = [
            column
            for column in feature_columns
            if column != "gender"
        ]

        for column in numeric_columns:

            values = X[column]

            invalid_type = values.map(
                lambda value: (
                    value is not None
                    and not isinstance(
                        value,
                        (int, float)
                    )
                )
            )

            if invalid_type.any():

                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{column} must be numeric or null."
                    ),
                )

            X[column] = pd.to_numeric(
                values,
                errors="raise",
            )

            if np.isinf(
                X[column].to_numpy(
                    dtype=float
                )
            ).any():

                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"{column} cannot be infinite."
                    ),
                )


        if "gender" in X.columns:

            valid_gender = {
                "F",
                "M",
                "U",
            }

            if not X["gender"].dropna().isin(
                valid_gender
            ).all():

                raise HTTPException(
                    status_code=422,
                    detail=(
                        "gender must be F, M, U, or null."
                    ),
                )

            X["gender"] = X[
                "gender"
            ].replace(
                {None: np.nan}
            )

        return client_ids, X


    # --------------------------------------------------------
    # Shared scoring function
    #
    # Both /score and /decide use this one implementation.
    # We do not duplicate prediction logic across endpoints.
    # --------------------------------------------------------

    def score_customers(customers, bundle):

        client_ids, X = prepare_customers(
            customers,
            bundle,
        )

        p_treatment = (
            bundle["treatment_model"]
            .predict_proba(X)[:, 1]
        )

        p_control = (
            bundle["control_model"]
            .predict_proba(X)[:, 1]
        )

        scores = pd.DataFrame(
            {
                "client_id": client_ids,
                "p_treatment": p_treatment,
                "p_control": p_control,
                "predicted_uplift": (
                    p_treatment - p_control
                ),
            }
        )

        probabilities = scores[
            ["p_treatment", "p_control"]
        ].to_numpy()

        if (
            not np.isfinite(probabilities).all()
            or not (
                (probabilities >= 0)
                & (probabilities <= 1)
            ).all()
        ):

            raise HTTPException(
                status_code=500,
                detail="Model returned invalid probabilities.",
            )

        return scores


    # --------------------------------------------------------
    # Health endpoint
    # --------------------------------------------------------

    @app.get("/health")
    def health(request: Request):

        bundle = request.app.state.model_bundle

        return {
            "status": "ok",
            "model_loaded": bundle is not None,
            "mlflow_run_id":
                bundle["mlflow_run_id"],
        }


    # --------------------------------------------------------
    # Model metadata endpoint
    #
    # Makes the deployed model version inspectable.
    # --------------------------------------------------------

    @app.get("/model-info")
    def model_info(request: Request):

        bundle = request.app.state.model_bundle

        return {
            "model_family": "logistic_t_learner",
            "mlflow_run_id":
                bundle["mlflow_run_id"],
            "feature_cutoff":
                bundle["feature_cutoff"],
            "feature_count":
                len(bundle["feature_columns"]),
            "feature_columns":
                bundle["feature_columns"],
        }


    # --------------------------------------------------------
    # Customer uplift scoring
    # --------------------------------------------------------

    @app.post("/score")
    def score(
        payload: ScoreRequest,
        request: Request,
    ):

        bundle = request.app.state.model_bundle

        scores = score_customers(
            payload.customers,
            bundle,
        )

        return {
            "mlflow_run_id":
                bundle["mlflow_run_id"],
            "customers_scored": len(scores),
            "predictions":
                scores.to_dict(
                    orient="records"
                ),
        }


    # --------------------------------------------------------
    # Budget-constrained treatment decisioning
    #
    # Reuse src/decisioning.py from Notebook 05.
    # Do not implement a second optimizer in the API.
    # --------------------------------------------------------

    @app.post("/decide")
    def decide(
        payload: DecisionRequest,
        request: Request,
    ):

        bundle = request.app.state.model_bundle

        scores = score_customers(
            payload.customers,
            bundle,
        )

        try:

            decisions = build_contact_policy(
                scores=scores,
                conversion_value=payload.conversion_value,
                contact_cost=payload.contact_cost,
                budget=payload.budget,
            )

            selected_ids = decisions.loc[
                decisions["contact"],
                "client_id",
            ]

            summary = summarize_policy(
                scores=scores,
                selected_client_ids=selected_ids,
                conversion_value=payload.conversion_value,
                contact_cost=payload.contact_cost,
                budget=payload.budget,
                policy_name="Uplift optimized",
            )

        except ValueError as error:

            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error


        return {
            "mlflow_run_id":
                bundle["mlflow_run_id"],
            "scenario": {
                "conversion_value":
                    payload.conversion_value,
                "contact_cost":
                    payload.contact_cost,
                "budget":
                    payload.budget,
            },
            "summary": summary,
            "decisions":
                decisions.to_dict(
                    orient="records"
                ),
        }


    return app


app = create_app()