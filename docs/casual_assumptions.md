# Causal Assumptions

## Treatment timing

Historical purchase behavior is used only from the pre-communication
feature period established by the project feature cutoff.

Treatment and target variables are never used to generate customer features.

## Treatment assignment

The available X5 dataset does not establish that treatment assignment was
randomized.

Therefore, raw treatment-control outcome differences are described as
observed differences rather than automatically interpreted as causal effects.

## Observed-confounding diagnostics

The project evaluates:

- standardized mean differences
- propensity-score predictability
- treatment/control propensity overlap
- inverse-probability weighting

These methods assess and adjust for observed differences between the treatment
groups.

## Causal interpretation

A causal interpretation of adjusted estimates requires assumptions including:

- consistency
- positivity / overlap
- correct model specification
- no unmeasured confounding

These assumptions cannot be fully verified from the observed dataset.

## Uplift modeling

The project estimates heterogeneous treatment response in order to rank
customers by predicted incremental response.

Model rankings are evaluated separately from ordinary outcome-prediction
performance.