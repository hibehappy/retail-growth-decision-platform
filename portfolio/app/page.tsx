import { Architecture } from "@/components/Architecture";
import { DecisionSimulator } from "@/components/DecisionSimulator";
import { DriftSummary } from "@/components/DriftSummary";
import { ModelComparison } from "@/components/ModelComparison";
import { GITHUB_REPO_URL, platformStats } from "@/lib/project-data";

export default function Home() {
  const githubConfigured = !GITHUB_REPO_URL.includes("YOUR_GITHUB_USERNAME");

  return (
    <main>
      <nav className="top-nav" aria-label="Primary navigation">
        <a className="brand" href="#top">Retail Growth</a>
        <div className="nav-links">
          <a href="#simulator">Simulator</a>
          <a href="#model">Model</a>
          <a href="#monitoring">Monitoring</a>
          <a href="#architecture">Architecture</a>
        </div>
        {githubConfigured ? (
          <a className="nav-button" href={GITHUB_REPO_URL} target="_blank" rel="noreferrer">GitHub ↗</a>
        ) : (
          <span className="nav-button nav-button-disabled" title="Set GITHUB_REPO_URL in lib/project-data.ts">GitHub URL not set</span>
        )}
      </nav>

      <section id="top" className="hero">
        <div className="hero-kicker">END-TO-END DATA + ML DECISION SYSTEM</div>
        <h1>Retail Growth<br /><span>Decision Platform</span></h1>
        <p className="hero-copy">
          Transforming more than 45.7 million retail purchase-item records into customer-level features, heterogeneous treatment-uplift estimates, and budget-constrained treatment decisions.
        </p>
        <div className="hero-actions">
          <a href="#simulator" className="primary-button">Explore the decision simulator</a>
          {githubConfigured && (
            <a href={GITHUB_REPO_URL} target="_blank" rel="noreferrer" className="secondary-button">View repository ↗</a>
          )}
        </div>

        <div className="stats-grid">
          {platformStats.map((stat) => (
            <div className="stat-card" key={stat.label}>
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="question-strip">
        <span className="question-label">Why uplift?</span>
        <p>
          Traditional response modeling asks who is likely to convert. This project asks who is more likely to convert <strong>because they receive the treatment</strong>.
        </p>
        <div className="formula">P(Y=1 | X, treatment) − P(Y=1 | X, control)</div>
      </section>

      <DecisionSimulator />
      <ModelComparison />
      <DriftSummary />
      <Architecture />

      <section className="section-shell docs-section">
        <div className="eyebrow">Technical depth</div>
        <h2>GitHub holds the implementation details</h2>
        <p className="section-copy">
          The public site is deliberately lightweight. The repository contains the notebooks, dbt project, tests, Airflow DAG, Kafka/Spark demo, FastAPI serving layer, model card, data dictionary, causal assumptions, and governance documentation.
        </p>
        {githubConfigured ? (
          <div className="docs-links">
            <RepoLink href={`${GITHUB_REPO_URL}/blob/main/docs/system_architecture.md`} title="System architecture" />
            <RepoLink href={`${GITHUB_REPO_URL}/blob/main/docs/model_card.md`} title="Model card" />
            <RepoLink href={`${GITHUB_REPO_URL}/blob/main/docs/data_dictionary.md`} title="Data dictionary" />
            <RepoLink href={`${GITHUB_REPO_URL}/tree/main/notebooks`} title="Notebooks" />
          </div>
        ) : (
          <div className="config-note">Before deploying, replace <code>YOUR_GITHUB_USERNAME</code> in <code>lib/project-data.ts</code>.</div>
        )}
      </section>

      <footer>
        <div>
          <strong>Retail Growth Decision Platform</strong>
          <p>Portfolio demonstration using the X5 RetailHero benchmark dataset.</p>
        </div>
        <p className="footer-note">Modeled economic results are scenario estimates, not realized campaign outcomes.</p>
      </footer>
    </main>
  );
}

function RepoLink({ href, title }: { href: string; title: string }) {
  return <a className="repo-link" href={href} target="_blank" rel="noreferrer">{title}<span>↗</span></a>;
}
