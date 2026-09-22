
# ============================================================
# Retail Growth Decisioning API
#
# Build context: repository root
#
# docker build -f api/Dockerfile -t retail-growth-api .
# ============================================================

FROM python:3.10-slim

# Keep Python output immediate and avoid unnecessary
# .pyc files inside the container.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install only serving dependencies.
# The API does not need MLflow, dbt, or Jupyter at runtime.
COPY api/requirements.txt /app/api/requirements.txt

RUN python -m pip install \
    --no-cache-dir \
    -r /app/api/requirements.txt

# Copy application code and the existing decision engine.
COPY api /app/api
COPY src /app/src

# Prepare the mount location for the serving artifact.
RUN mkdir -p /app/data/deployment

EXPOSE 8000

# The model is loaded from the read-only volume at startup.
ENV MODEL_BUNDLE_PATH=/app/data/deployment/model_bundle.joblib

CMD ["python", "-m", "uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]