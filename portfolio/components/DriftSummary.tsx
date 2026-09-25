export function DriftSummary() {
  return (
    <section id="monitoring" className="section-shell">
      <div className="eyebrow">Data & model monitoring</div>
      <div className="section-heading-row">
        <div>
          <h2>Stable benchmark populations, then a controlled stress test</h2>
          <p className="section-copy">
            The real training/scoring comparison remained highly stable. A deliberately shifted synthetic population was then used to verify that the detector raises meaningful alerts.
          </p>
        </div>
      </div>

      <div className="drift-columns">
        <div className="drift-panel drift-panel-ok">
          <div className="drift-topline"><span>Observed benchmark comparison</span><strong>OK</strong></div>
          <div className="drift-big">34 / 34</div>
          <p>Model features remained within the project&apos;s normal drift range.</p>
          <dl>
            <div><dt>Highest feature PSI</dt><dd>0.000204</dd></div>
            <div><dt>Prediction PSI</dt><dd>0.000086</dd></div>
            <div><dt>Warnings / critical</dt><dd>0 / 0</dd></div>
          </dl>
        </div>

        <div className="drift-panel drift-panel-warning">
          <div className="drift-topline"><span>Controlled synthetic shift</span><strong>WARNING</strong></div>
          <div className="drift-big">2 critical + 1 warning</div>
          <p>Known feature shifts propagated into the model&apos;s prediction distribution.</p>
          <dl>
            <div><dt>Prediction PSI</dt><dd>0.17661</dd></div>
            <div><dt>Critical features</dt><dd>2</dd></div>
            <div><dt>Warning features</dt><dd>1</dd></div>
          </dl>
        </div>
      </div>

      <p className="fine-print">A drift alert is an investigation signal, not proof that the model has become inaccurate. Real performance drift requires new treatment assignments and observed outcomes.</p>
    </section>
  );
}
