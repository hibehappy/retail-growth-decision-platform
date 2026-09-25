import { modelMetrics } from "@/lib/project-data";

function formatMetric(metric: string, value: number) {
  if (metric === "Qini") return value.toFixed(2);
  return value.toFixed(4);
}

export function ModelComparison() {
  return (
    <section id="model" className="section-shell">
      <div className="eyebrow">Model selection</div>
      <div className="section-heading-row">
        <div>
          <h2>The best classifier was not automatically the best decision model</h2>
          <p className="section-copy">
            A gradient-boosted T-learner improved ordinary outcome prediction, while the logistic T-learner produced the stronger Qini and uplift-at-30% used for the treatment-ranking objective.
          </p>
        </div>
        <span className="pill pill-selected">Selected: Logistic T-learner</span>
      </div>

      <div className="model-layout">
        <div className="model-table-card">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Logistic</th>
                <th>Boosted</th>
                <th>Best aligned</th>
              </tr>
            </thead>
            <tbody>
              {modelMetrics.map((row) => {
                const lowerIsBetter = row.objective === "prediction-lower";
                const logisticWins = lowerIsBetter
                  ? row.logistic < row.boosted
                  : row.logistic > row.boosted;
                return (
                  <tr key={row.metric}>
                    <td>{row.metric}</td>
                    <td className={logisticWins ? "winner" : ""}>{formatMetric(row.metric, row.logistic)}</td>
                    <td className={!logisticWins ? "winner" : ""}>{formatMetric(row.metric, row.boosted)}</td>
                    <td>{row.objective.startsWith("prediction") ? "Prediction" : "Decisioning"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="insight-stack">
          <div className="insight-card">
            <span className="insight-number">168.37</span>
            <strong>Qini</strong>
            <p>Logistic T-learner, versus 137.73 for the boosted alternative.</p>
          </div>
          <div className="insight-card">
            <span className="insight-number">6.36 pp</span>
            <strong>Observed uplift @ 30%</strong>
            <p>The primary ranking slice used for the downstream decision story.</p>
          </div>
          <div className="insight-card insight-card-muted">
            <strong>Causal limitation</strong>
            <p>The public X5 materials used in the project do not establish randomized treatment assignment. Observed balance does not rule out unmeasured confounding.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
