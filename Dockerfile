# Multi-stage: build Vite SPA, then Python workspace with uv.
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY packages ./packages
COPY orchestrator ./orchestrator

RUN uv sync --frozen --all-packages

COPY --from=frontend-build /fe/dist ./frontend/dist

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONUNBUFFERED=1
ENV STATIC_DIR=/app/frontend/dist

EXPOSE 8080 8001 8002 8003

# Default: orchestrator API (override in compose for agents)
CMD ["uvicorn", "orchestrator.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
