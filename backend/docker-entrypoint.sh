#!/usr/bin/env sh
# Bootstrap the API container against Postgres, then hand off to the command
# (uvicorn by default). All three steps are idempotent and cheap on a warm
# database, so this runs safely on every boot.
set -eu

cd /app/backend

echo "→ applying migrations…"
alembic upgrade head

# no-op when the dataset is already in Postgres; on an empty database this
# loads the committed dataset, generating one first if this image was built
# without it
echo "→ checking dataset…"
python scripts/seed_db.py

# no-op when a model for this code + dataset already exists in Postgres. That
# is what stops a rebuild, a fresh machine or a second replica from retraining.
echo "→ checking model…"
python scripts/train.py --ensure

echo "→ api ready on :8000"
exec "$@"
