#!/usr/bin/env sh
# Bootstrap the API container: generate the synthetic dataset and train the
# models on first boot, then hand off to the command (uvicorn by default).
# Mirrors run.sh, so a fresh volume behaves like a fresh checkout.
set -eu

cd /app/backend

if [ ! -f /app/data/transactions.parquet ]; then
  echo "→ generating synthetic Bharat (500 customers, 12 months)…"
  python scripts/generate_data.py
fi

if [ ! -f /app/backend/models/arthsaathi.joblib ]; then
  echo "→ training models…"
  python scripts/train.py
fi

echo "→ api ready on :8000"
exec "$@"
