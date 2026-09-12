#!/usr/bin/env sh
# Bootstrap the API container, then hand off to the command (uvicorn by
# default).
#
# Both checks below are a fallback, not the normal path: the image ships the
# committed dataset and the trained model, and a fresh named volume is seeded
# from them, so neither branch usually runs. They only fire when the image was
# built without the dataset context, or when the artefacts were deleted —
# in which case this mirrors run.sh and a fresh volume behaves like a fresh
# checkout.
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
