export function Architecture() {
  return (
    <section id="architecture" className="section-shell">
      <div className="eyebrow">Platform architecture</div>
      <div className="section-heading-row">
        <div>
          <h2>One decision system, five engineering layers</h2>
          <p className="section-copy">
            The historical X5 workflow is the modeling source of truth. Incremental ingestion and Kafka/Spark remain isolated synthetic demonstrations so they do not contaminate historical training or business metrics.
          </p>
        </div>
      </div>

      <div className="architecture-image-wrap">
        <img
          src="/architecture_overview.png"
          alt="Retail Growth Decision Platform architecture from X5 source data through Snowflake, dbt, uplift modeling, decisioning, model serving, reliability and governance."
        />
      </div>

      <div className="stack-grid">
        <StackCard title="Data engineering" body="Amazon S3 → Snowflake → dbt → analytical and feature marts" />
        <StackCard title="Data science" body="Uplift modeling → causal diagnostics → model comparison → drift monitoring" />
        <StackCard title="Decision science" body="Predicted uplift → modeled value → budget-constrained contact policy" />
        <StackCard title="ML engineering" body="MLflow → deployment bundle → FastAPI → Docker" />
        <StackCard title="Reliability & governance" body="Airflow → CI → streaming → lineage → provenance" />
      </div>
    </section>
  );
}

function StackCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="stack-card">
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  );
}
