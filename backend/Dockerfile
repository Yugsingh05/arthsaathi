# ArthSaathi API — FastAPI + uv
#
# Build context is the REPO ROOT, not backend/, because app/core/engine.py
# resolves DATA as backend/../data — the two directories must stay siblings.
#   docker build -f backend/Dockerfile -t arthsaathi-api .

# ---------- stage 1: resolve dependencies into a venv --------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS deps

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app/backend

# lockfile only, so this layer is cached until dependencies actually change
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# ---------- stage 2: runtime --------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

# libgomp1 is required by xgboost and scikit-learn's OpenMP paths
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=deps /opt/venv /opt/venv

WORKDIR /app/backend
COPY backend/ ./
COPY docker/api-entrypoint.sh /usr/local/bin/api-entrypoint
RUN chmod +x /usr/local/bin/api-entrypoint

# Run unprivileged. Both of these become volume mount points, and a named
# volume inherits ownership from the image directory it first covers — so
# chowning them here is what lets the container write to them later.
RUN useradd --create-home --uid 1000 app \
 && mkdir -p /app/data /app/backend/models \
 && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=180s --retries=20 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).status==200 else 1)"

ENTRYPOINT ["api-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
