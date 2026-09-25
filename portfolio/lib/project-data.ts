export const GITHUB_REPO_URL =
  "https://github.com/hibehappy/retail-growth-decision-platform";

export const decisionScenarios = [
  {
    budget: 0,
    contacts: 0,
    contactPct: 0,
    incrementalConversions: 0,
    incrementalValue: 0,
    contactSpend: 0,
    netValue: 0,
  },
  {
    budget: 2500,
    contacts: 10000,
    contactPct: 4.997,
    incrementalConversions: 1253.93,
    incrementalValue: 25078.57,
    contactSpend: 2500,
    netValue: 22578.57,
  },
  {
    budget: 5000,
    contacts: 20000,
    contactPct: 9.994,
    incrementalConversions: 2066.17,
    incrementalValue: 41323.31,
    contactSpend: 5000,
    netValue: 36323.31,
  },
  {
    budget: 10000,
    contacts: 40000,
    contactPct: 19.988,
    incrementalConversions: 3291.91,
    incrementalValue: 65838.15,
    contactSpend: 10000,
    netValue: 55838.15,
  },
  {
    budget: 20000,
    contacts: 80000,
    contactPct: 39.975,
    incrementalConversions: 4980.83,
    incrementalValue: 99616.53,
    contactSpend: 20000,
    netValue: 79616.53,
  },
] as const;

export const modelMetrics = [
  { metric: "Treatment ROC-AUC", logistic: 0.765062, boosted: 0.77669, objective: "prediction" },
  { metric: "Control ROC-AUC", logistic: 0.772814, boosted: 0.782102, objective: "prediction" },
  { metric: "Treatment Brier", logistic: 0.186098, boosted: 0.181828, objective: "prediction-lower" },
  { metric: "Control Brier", logistic: 0.188313, boosted: 0.184455, objective: "prediction-lower" },
  { metric: "Qini", logistic: 168.366182, boosted: 137.729506, objective: "decision" },
  { metric: "AUUC", logistic: 0.061673, boosted: 0.062355, objective: "decision" },
  { metric: "Uplift @ 30%", logistic: 0.063582, boosted: 0.059267, objective: "decision" },
] as const;

export const platformStats = [
  { label: "Purchase-item records", value: "45.7M+" },
  { label: "Customer transactions", value: "8.0M+" },
  { label: "Customers", value: "400K+" },
  { label: "Model features", value: "34" },
] as const;
