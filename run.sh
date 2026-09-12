#!/usr/bin/env bash
# One command to bring ArthSaathi up. Ctrl-C stops both halves.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f data/transactions.parquet ]; then
  echo "→ generating synthetic Bharat (500 customers, 12 months)…"
  (cd backend && uv run python scripts/generate_data.py)
fi
if [ ! -f backend/models/arthsaathi.joblib ]; then
  echo "→ training models…"
  (cd backend && uv run python scripts/train.py)
fi

echo "→ api  http://localhost:8000/docs"
(cd backend && uv run uvicorn app.main:app --port 8000) &
API=$!
echo "→ web  http://localhost:5173"
(cd frontend && npm run dev -- --port 5173) &
WEB=$!
trap 'kill $API $WEB 2>/dev/null' EXIT INT TERM
wait
