"""The trained model, stored in Postgres instead of on a disk somewhere.

Training used to run whenever a container met an empty volume, which meant a
fresh machine, a wiped volume or a second stack each paid for it again. The
artifact now lives in a table, keyed by a fingerprint of everything that can
change its contents: the modelling code, the policy rules, and the size and
as-of date of the dataset it was fitted on.

Boot looks the fingerprint up. A hit is a download; a miss trains once and
stores the result for every other container, machine and rebuild.
"""
from __future__ import annotations

import hashlib
import io
import logging
from pathlib import Path

import joblib
from sqlalchemy import select, text

from app.db.models import ModelArtifact
from app.db.session import Session

log = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# every file whose contents can change what a trained model looks like
FINGERPRINT_SOURCES = [
    "app/core/features.py",
    "app/core/segments.py",
    "app/core/propensity.py",
    "app/core/stress.py",
    "app/core/fraud.py",
    "app/core/policy.py",
    "scripts/train.py",
    "policies/rules.yaml",
]


def fingerprint() -> str:
    h = hashlib.sha256()
    for rel in FINGERPRINT_SOURCES:
        path = BACKEND_ROOT / rel
        h.update(rel.encode())
        h.update(path.read_bytes() if path.exists() else b"<missing>")

    # the data matters too: same code over a different dataset is a different
    # model, so fold in the row counts and the as-of date
    with Session() as s:
        rows = s.execute(text("SELECT count(*) FROM transactions")).scalar_one()
        custs = s.execute(text("SELECT count(*) FROM customers")).scalar_one()
        as_of = s.execute(
            text("SELECT payload->>'today' FROM documents WHERE name='demo_checkpoints'")
        ).scalar_one_or_none()
    h.update(f"{rows}:{custs}:{as_of}".encode())
    return h.hexdigest()


def load(fp: str | None = None) -> dict | None:
    """Fetch and deserialise the artifact for this fingerprint, if it exists."""
    fp = fp or fingerprint()
    with Session() as s:
        blob = s.execute(
            select(ModelArtifact.blob).where(ModelArtifact.fingerprint == fp)
        ).scalar_one_or_none()
    if blob is None:
        return None
    log.info("loaded model artifact %s from postgres (%.1f MB)", fp[:12], len(blob) / 1e6)
    return joblib.load(io.BytesIO(blob))


def save(artifact: dict, *, fp: str | None = None, rows_trained_on: int | None = None) -> str:
    fp = fp or fingerprint()
    buf = io.BytesIO()
    joblib.dump(artifact, buf)
    blob = buf.getvalue()

    with Session() as s:
        s.execute(
            text("""
                INSERT INTO model_artifacts
                    (fingerprint, blob, trained_at, auc, rows_trained_on)
                VALUES (:fp, :blob, :trained_at, CAST(:auc AS jsonb), :rows)
                ON CONFLICT (fingerprint) DO UPDATE SET
                    blob = EXCLUDED.blob,
                    trained_at = EXCLUDED.trained_at,
                    auc = EXCLUDED.auc,
                    rows_trained_on = EXCLUDED.rows_trained_on
            """),
            {
                "fp": fp,
                "blob": blob,
                "trained_at": str(artifact.get("trained_at", "")),
                "auc": __import__("json").dumps(artifact.get("auc", {})),
                "rows": rows_trained_on,
            },
        )
        s.commit()
    log.info("stored model artifact %s in postgres (%.1f MB)", fp[:12], len(blob) / 1e6)
    return fp
