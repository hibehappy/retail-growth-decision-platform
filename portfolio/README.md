# Retail Growth Portfolio Site

A lightweight public-facing demo for the Retail Growth Decision Platform.

The site intentionally uses **precomputed, verified project results** rather than exposing Snowflake credentials, AWS credentials, raw X5 data, MLflow state, or the local model artifact.

## 1. Copy into the main repository

Place this entire folder at:

```text
retail-growth-decision-platform/
└── portfolio/
```

## 2. Set your GitHub repository URL

Open:

```text
portfolio/lib/project-data.ts
```

Replace:

```ts
https://github.com/YOUR_GITHUB_USERNAME/retail-growth-decision-platform
```

with your real repository URL.

This is the only project-specific configuration required.

## 3. Run locally

From the repository root:

```bash
cd portfolio
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## 4. Production build

```bash
npm run build
```

A successful build confirms the public site compiles independently from the Python/Snowflake project environment.

## 5. Deploy with Vercel

1. Push the `portfolio/` folder to the existing GitHub repository.
2. Sign in to Vercel with GitHub.
3. Choose **Add New → Project**.
4. Import `retail-growth-decision-platform`.
5. Set **Root Directory** to `portfolio`.
6. Leave Framework Preset as **Next.js**.
7. Click **Deploy**.

No environment variables are required for this static portfolio version.

After deployment, Vercel provides a public URL such as:

```text
https://retail-growth-decision-platform.vercel.app
```

Add that URL to the GitHub repository **Website** field and optionally to the top of the main project README.

## Site contents

- Hero summary and project metrics
- Interactive decision-budget simulator using verified Notebook 05 scenarios
- Logistic vs. boosted T-learner comparison
- Data/model drift monitoring summary
- Final platform architecture visual
- Links back to the technical GitHub repository

## Safety / data boundary

This public site does not contain:

- `.env`
- Snowflake credentials
- AWS credentials
- raw X5 files
- local model artifacts
- MLflow database/state
- Airflow database/state
- generated customer-level scoring data

The incremental and Kafka/Spark demonstrations remain synthetic and isolated from the historical X5 modeling workflow.
