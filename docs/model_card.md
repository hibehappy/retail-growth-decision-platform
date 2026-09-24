# Retail Growth Uplift Model — Model Card

## Model purpose

The model estimates heterogeneous treatment uplift for customers in the X5 RetailHero benchmark dataset.

Its intended use in this project is to prioritize customers for a treatment or marketing contact under an explicit economic constraint.

The model does not determine whether a customer should receive a legally or ethically consequential treatment.

## Model architecture

The selected decisioning model is a logistic-regression T-learner.

Two independent outcome models estimate:

- P(Y = 1 | X, treatment)
- P(Y = 1 | X, control)

Predicted uplift is calculated as:

predicted uplift =
P(Y = 1 | X, treatment)
-
P(Y = 1 | X, control)

## Development data

Model-development population:

**200,039 customers**

Scoring population:

**200,123 customers**

The model uses **34 features** generated through the Snowflake/dbt feature pipeline.

## Development evaluation

On the development holdout, the logistic T-learner achieved:

- Treatment ROC-AUC: **0.765062**
- Control ROC-AUC: **0.772814**
- Treatment Brier score: **0.186098**
- Control Brier score: **0.188313**
- Qini: **168.366182**
- Observed uplift in top 30%: **0.063582**

These metrics belong to the development models evaluated on the held-out subset.

The later full-data model used for scoring was refit on all available training customers and therefore does not have an independent labeled holdout of its own.

## Causal limitations

The public X5 materials used in this project do not establish that treatment assignment was randomized.

Observed covariates were highly balanced and an out-of-fold propensity model produced ROC-AUC near 0.5, but those findings do not prove randomization or rule out unobserved confounding.

Accordingly, modeled uplift should be interpreted under the documented causal assumptions rather than as experimentally verified individual treatment effects.

## Decision policy

The demonstration decision policy combines predicted uplift with:

- conversion value
- contact cost
- budget

The primary example uses:

- conversion value: **20**
- contact cost: **0.25**
- budget: **10,000**

Under those assumptions, the scoring policy selected **40,000 customers**.

These economic values are demonstration assumptions rather than observed business economics from X5.

## Monitoring

The model is monitored for:

- feature-distribution drift
- missingness changes
- predicted-uplift drift
- downstream treatment-policy changes

Across the benchmark development and scoring populations, all **34 model features** remained within the project's normal drift range.

The prediction PSI was approximately **0.000086**, classified as **OK**.

A controlled synthetic drift experiment successfully generated WARNING and CRITICAL alerts, demonstrating that the monitoring logic responds to known distribution changes.

## Artifact governance

The deployed model artifact is fingerprinted using SHA-256.

Model lineage and feature provenance are derived from the dbt transformation graph and model metadata.

Relevant generated governance metadata is stored separately from the source code.

## Known limitations

This project uses a historical benchmark rather than a live production treatment system.

The scoring dataset does not contain observed treatment outcomes, so true post-deployment uplift-performance drift cannot be measured.

The decision-policy economics are illustrative.

The current deployment is a local demonstration rather than a production multi-user service.

## Intended extensions

A production system could add:

- realized treatment-outcome monitoring
- scheduled drift checks
- model approval workflows
- artifact registry permissions
- automated retraining review
- retention policies
- production audit logging