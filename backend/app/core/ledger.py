from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd

PURPOSES = {
    "personalisation": "Suggesting products that fit your money",
    "stress_watch": "Spotting a difficult month early and offering help",
    "fraud_watch": "Protecting your account from unusual transfers",
}


class Ledger:
    def __init__(self, db_path: str | Path):
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.con = duckdb.connect(str(self.path))
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                entry_id VARCHAR PRIMARY KEY, ts TIMESTAMP, customer_id VARCHAR,
                as_of DATE, purpose VARCHAR, kind VARCHAR, product_id VARCHAR,
                shown BOOLEAN, score DOUBLE, suppressed_by VARCHAR,
                reason_codes VARCHAR, features_used VARCHAR, detail VARCHAR)""")
        self.con.execute("""
            CREATE TABLE IF NOT EXISTS consents (
                customer_id VARCHAR, purpose VARCHAR, granted BOOLEAN,
                updated_at TIMESTAMP, PRIMARY KEY (customer_id, purpose))""")

    def seed_consents(self, customers: pd.DataFrame) -> None:
        with self._lock:
            rows = []
            for r in customers.to_dict("records"):
                for p in PURPOSES:
                    rows.append((r["customer_id"], p, bool(r.get(f"consent_{p}", True)), datetime.now()))
            self.con.executemany(
                "INSERT OR REPLACE INTO consents VALUES (?,?,?,?)", rows)

    def consents(self, customer_id: str) -> dict[str, bool]:
        with self._lock:
            rows = self.con.execute(
                "SELECT purpose, granted FROM consents WHERE customer_id=?", [customer_id]).fetchall()
        return {p: bool(g) for p, g in rows} or {p: True for p in PURPOSES}

    def set_consent(self, customer_id: str, purpose: str, granted: bool) -> dict[str, bool]:
        with self._lock:
            self.con.execute("INSERT OR REPLACE INTO consents VALUES (?,?,?,?)",
                             [customer_id, purpose, granted, datetime.now()])
        self.write(customer_id, purpose=purpose, kind="consent_change", shown=None,
                   detail=f"{'granted' if granted else 'withdrawn'} by customer")
        return self.consents(customer_id)

    def write(self, customer_id: str, purpose: str, kind: str, *, as_of=None,
              product_id: str | None = None, shown: bool | None = None,
              score: float | None = None, suppressed_by: str | None = None,
              reason_codes: list[str] | None = None, features_used: list[str] | None = None,
              detail: str | None = None) -> str:
        eid = uuid.uuid4().hex[:12]
        with self._lock:
            self.con.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                [eid, datetime.now(), customer_id, as_of, purpose, kind, product_id,
                 shown, score, suppressed_by, json.dumps(reason_codes or []),
                 json.dumps(features_used or []), detail])
        return eid

    def entries(self, customer_id: str, limit: int = 100) -> list[dict]:
        with self._lock:
            df = self.con.execute(
                "SELECT * FROM ledger WHERE customer_id=? ORDER BY ts DESC LIMIT ?",
                [customer_id, limit]).df()
        if df.empty:
            return []
        df["reason_codes"] = df.reason_codes.map(json.loads)
        df["features_used"] = df.features_used.map(json.loads)
        df["ts"] = df.ts.dt.strftime("%Y-%m-%d %H:%M")
        df["as_of"] = df.as_of.astype(str)
        return df.where(pd.notna(df), None).to_dict("records")

    def counts(self) -> dict:
        with self._lock:
            held = self.con.execute(
                "SELECT count(*) FROM ledger WHERE kind='recommendation' AND shown=false").fetchone()[0]
            shown = self.con.execute(
                "SELECT count(*) FROM ledger WHERE kind='recommendation' AND shown=true").fetchone()[0]
        return {"offers_shown": int(shown), "offers_held_back": int(held)}
