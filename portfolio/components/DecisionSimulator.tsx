"use client";

import { useMemo, useState } from "react";
import { decisionScenarios } from "@/lib/project-data";

const money = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 2,
  minimumFractionDigits: 2,
});

const whole = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
});

export function DecisionSimulator() {
  const [scenarioIndex, setScenarioIndex] = useState(3);
  const scenario = decisionScenarios[scenarioIndex];

  const points = useMemo(() => {
    const width = 680;
    const height = 180;
    const padX = 24;
    const padY = 18;
    const max = Math.max(...decisionScenarios.map((row) => row.netValue));
    return decisionScenarios.map((row, index) => ({
      x: padX + (index / (decisionScenarios.length - 1)) * (width - padX * 2),
      y: height - padY - (row.netValue / max) * (height - padY * 2),
      ...row,
    }));
  }, []);

  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <section id="simulator" className="section-shell">
      <div className="eyebrow">Decision simulator</div>
      <div className="section-heading-row">
        <div>
          <h2>From predicted uplift to an economic policy</h2>
          <p className="section-copy">
            Explore the verified Notebook 05 budget scenarios. Conversion value is fixed at 20 and contact cost at 0.25 so the demo never invents model outputs that were not actually evaluated.
          </p>
        </div>
        <span className="pill">Precomputed verified results</span>
      </div>

      <div className="sim-grid">
        <div className="control-panel">
          <label htmlFor="budget">Campaign budget</label>
          <div className="budget-value">{whole.format(scenario.budget)}</div>
          <input
            id="budget"
            aria-label="Campaign budget scenario"
            type="range"
            min="0"
            max={decisionScenarios.length - 1}
            step="1"
            value={scenarioIndex}
            onChange={(event) => setScenarioIndex(Number(event.target.value))}
          />
          <div className="range-labels">
            {decisionScenarios.map((row) => (
              <span key={row.budget}>{row.budget === 0 ? "0" : `${row.budget / 1000}k`}</span>
            ))}
          </div>
          <div className="assumption-list">
            <div><span>Conversion value</span><strong>20</strong></div>
            <div><span>Contact cost</span><strong>0.25</strong></div>
            <div><span>Scoring population</span><strong>200,123</strong></div>
          </div>
        </div>

        <div className="metric-grid" aria-live="polite">
          <MetricCard label="Customers selected" value={whole.format(scenario.contacts)} sub={`${scenario.contactPct.toFixed(2)}% of scoring population`} />
          <MetricCard label="Incremental conversions" value={money.format(scenario.incrementalConversions)} sub="Modeled" />
          <MetricCard label="Incremental value" value={money.format(scenario.incrementalValue)} sub="Modeled" />
          <MetricCard label="Modeled net value" value={money.format(scenario.netValue)} sub="After contact spend" emphasis />
        </div>
      </div>

      <div className="chart-card">
        <div className="chart-title-row">
          <div>
            <h3>Budget sensitivity</h3>
            <p>Modeled net value rises as the budget allows more high-uplift customers to be contacted.</p>
          </div>
          <div className="chart-highlight">Selected: {whole.format(scenario.budget)}</div>
        </div>
        <svg viewBox="0 0 680 205" className="budget-chart" role="img" aria-label="Modeled net value by campaign budget">
          <line x1="24" y1="162" x2="656" y2="162" className="axis-line" />
          <polyline points={polyline} className="chart-line" />
          {points.map((point, index) => (
            <g key={point.budget}>
              <circle
                cx={point.x}
                cy={point.y}
                r={index === scenarioIndex ? 8 : 5}
                className={index === scenarioIndex ? "chart-dot active" : "chart-dot"}
              />
              <text x={point.x} y="187" textAnchor="middle" className="chart-label">
                {point.budget === 0 ? "0" : `${point.budget / 1000}k`}
              </text>
            </g>
          ))}
        </svg>
        <p className="fine-print">Prediction-based scenario estimates, not realized campaign outcomes.</p>
      </div>
    </section>
  );
}

function MetricCard({
  label,
  value,
  sub,
  emphasis = false,
}: {
  label: string;
  value: string;
  sub: string;
  emphasis?: boolean;
}) {
  return (
    <div className={emphasis ? "metric-card metric-card-emphasis" : "metric-card"}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{sub}</small>
    </div>
  );
}
