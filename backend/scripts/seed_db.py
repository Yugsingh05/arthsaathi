"""Load the dataset into Postgres.

Idempotent: with a populated database it does nothing, so the container
entrypoint can call it on every boot. Source of the rows, in order of
preference:

  1. the parquet/json files committed to this repo, if they are present
  2. a freshly generated synthetic dataset, if they are not

After this runs, the application never touches either — every read comes from
Postgres.

    uv run python scripts/seed_db.py           # seed if empty
    uv run python scripts/seed_db.py --force   # reload even if populated
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from sqlalchemy import text

from app.db.bulk import table_count, write_frame
from app.db.session import bulk_engine

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "data"
CASES = ROOT / "app" / "data" / "cases.json"

# table -> (parquet file, columns to write)
TABLES = {
    "customers": ("customers.parquet", None),
    "products": ("products.parquet", None),
    "emis": ("emis.parquet", None),
    "life_events": ("life_events.parquet", ["customer_id", "event_date", "event", "detail"]),
    "transactions": ("transactions.parquet", None),
}


def _ensure_dataset_files() -> None:
    """Generate the parquet files if this checkout does not have them."""
    if (DATA / "transactions.parquet").exists():
        return
    print("→ no dataset files found, generating a fresh synthetic one…")
    import subprocess

    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_data.py")], check=True)


def seed(force: bool = False) -> None:
    engine = bulk_engine()

    if not force and table_count(engine, "transactions") > 0:
        counts = {t: table_count(engine, t) for t in TABLES}
        print("→ database already seeded:",
              ", ".join(f"{k} {v:,}" for k, v in counts.items()))
        return

    _ensure_dataset_files()
    t0 = time.time()

    for table, (fname, cols) in TABLES.items():
        df = pd.read_parquet(DATA / fname)
        if table == "customers" and "account_opened" in df:
            df["account_opened"] = pd.to_datetime(df.account_opened).dt.date
        if table == "life_events" and "event_date" in df:
            df["event_date"] = pd.to_datetime(df.event_date).dt.date
        n = write_frame(engine, df, table, columns=cols)
        print(f"  {table:<14} {n:>8,} rows  ({time.time() - t0:.0f}s elapsed)")

    # exposures and the small JSON documents go in as JSONB
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE exposures"))
        exp_path = DATA / "exposures.json"
        rows = json.loads(exp_path.read_text()) if exp_path.exists() else []
        for row in rows:
            conn.execute(
                text("INSERT INTO exposures (exposure_id, payload) VALUES (:i, :p)"),
                {"i": row["exposure_id"], "p": json.dumps(row)},
            )
        print(f"  {'exposures':<14} {len(rows):>8,} rows")

        docs = {}
        if (DATA / "demo_checkpoints.json").exists():
            docs["demo_checkpoints"] = json.loads((DATA / "demo_checkpoints.json").read_text())
        if CASES.exists():
            docs["cases"] = json.loads(CASES.read_text())
        for name, payload in docs.items():
            conn.execute(
                text("""INSERT INTO documents (name, payload) VALUES (:n, :p)
                        ON CONFLICT (name) DO UPDATE SET payload = EXCLUDED.payload"""),
                {"n": name, "p": json.dumps(payload)},
            )
        print(f"  {'documents':<14} {len(docs):>8,} rows")

    print(f"→ seeded in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="reload even if populated")
    seed(**vars(ap.parse_args()))
