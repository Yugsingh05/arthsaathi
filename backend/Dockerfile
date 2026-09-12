# ArthSaathi API — FastAPI + uv. Self-contained: build context is this
# directory, nothing outside backend/ is needed.
#
#   cd backend && docker build -t arthsaathi-api .
#   cd backend && docker compose up --build
#
# Inside the image the tree is /app/backend (this directory) and /app/data,
# because app/core/engine.py resolves DATA as backend/../data.

# ---------- stage 0: the dataset ----------------------------------------
# data/ lives beside this directory, so it is outside the build context. The
# compose files pass it in as a named context; this empty default is what makes
# a bare `docker build .` from backend/ still work — /app/data comes out empty
# and the entrypoint generates it on first boot instead.
#
#   docker build --build-context dataset=../data -t arthsaathi-api .
FROM scratch AS dataset

# ---------- stage 1: resolve dependencies into a venv --------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS deps

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /src

# lockfile only, so this layer is cached until dependencies actually change
COPY pyproject.toml uv.lock ./
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
# brings models/arthsaathi.joblib in with the source, so no boot-time training
COPY . ./
RUN chmod +x docker-entrypoint.sh

# the committed dataset, or nothing at all if the context was not supplied
COPY --from=dataset . /app/data/

# Run unprivileged. /app/data and models/ both become volume mount points. A
# named volume is seeded from the image directory it first covers and inherits
# its ownership — which is why chowning here both lets the container write to
# them later and hands a fresh volume the baked-in data and model.
RUN useradd --create-home --uid 1000 app \
 && mkdir -p /app/data /app/backend/models \
 && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=180s --retries=20 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=3).status==200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
