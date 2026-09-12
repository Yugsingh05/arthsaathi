#!/usr/bin/env bash
# One command to bring ArthSaathi up. Ctrl-C stops both halves.
#
# Needs a Postgres URL in backend/.env — see backend/.env.example. The three
# setup steps are the same ones the container entrypoint runs, and each is a
# no-op once the database is warm.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -f backend/.env ]; then
  echo "backend/.env is missing. Copy backend/.env.example and put your"
  echo "Postgres URL in it, then run this again." >&2
  exit 1
fi

echo "→ applying migrations…"
(cd backend && uv run alembic upgrade head)

echo "→ checking dataset…"
(cd backend && uv run python scripts/seed_db.py)

echo "→ checking model…"
(cd backend && uv run python scripts/train.py --ensure)

echo "→ api  http://localhost:8000/docs"
(cd backend && uv run uvicorn app.main:app --port 8000) &
API=$!
echo "→ web  http://localhost:5173"
(cd frontend && npm run dev -- --port 5173) &
WEB=$!
trap 'kill $API $WEB 2>/dev/null' EXIT INT TERM
wait
