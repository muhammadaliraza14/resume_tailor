# syntax=docker/dockerfile:1
# Production image: Vite SPA + FastAPI + CrewAI (single uvicorn worker — in-memory job store).

FROM node:22-alpine AS frontend
WORKDIR /app/web/frontend
COPY web/frontend/package.json web/frontend/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci
COPY web/frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="resume_tailor" \
      org.opencontainers.image.description="Resume tailoring API (CrewAI) + static UI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOST=0.0.0.0 \
    PORT=8765 \
    RESUME_TAILOR_PROJECT_ROOT=/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --home-dir /home/app --create-home --shell /sbin/nologin app

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY src /app/src
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel \
    && pip install /app

COPY --from=frontend /app/web/frontend/dist /app/web/frontend/dist
COPY input /app/input

COPY docker/entrypoint.sh /docker/entrypoint.sh
COPY docker/cmd.sh /docker/cmd.sh
RUN chmod +x /docker/entrypoint.sh /docker/cmd.sh \
    && mkdir -p /app/output/web_jobs \
    && chown -R app:app /app

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=8s --start-period=120s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/health', timeout=5)"

ENTRYPOINT ["/docker/entrypoint.sh"]
