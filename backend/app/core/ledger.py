from __future__ import annotations

import uuid
from datetime import datetime

import pandas as pd
from sqlalchemy import Engine, func, select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import Consent, LedgerEntry
from app.db.session import Session

PURPOSES = {
    "personalisation": "Suggesting products that fit your money",
    "stress_watch": "Spotting a difficult month early and offering help",
    "fraud_watch": "Protecting your account from unusual transfers",
}


class Ledger:
    """Consent state and the decision audit trail, in Postgres.

    This used to be a duckdb file inside the container, which meant the record
    of what was shown to whom died with the container. It is now shared state:
    every replica reads and writes the same rows, and they survive a rebuild.
    """

    def __init__(self, engine: Engine | None = None):
        # kept for symmetry with the callers; sessions come from the shared
        # sessionmaker, which is already bound to the app engine
        self.engine = engine

    # ---------------------------------------------------------------- consents
    def seed_consents(self, customers: pd.DataFrame) -> None:
        """Insert the dataset's default consents, leaving any live ones alone.

        A customer who has since withdrawn consent must not have it silently
        restored on the next boot, so this is ON CONFLICT DO NOTHING.
        """
        rows = [
            {
                "customer_id": r["customer_id"],
                "purpose": p,
                "granted": bool(r.get(f"consent_{p}", True)),
                "updated_at": datetime.now(),
            }
            for r in customers.to_dict("records")
            for p in PURPOSES
        ]
        if not rows:
            return
        with Session() as s:
            stmt = insert(Consent).values(rows)
            s.execute(stmt.on_conflict_do_nothing(index_elements=["customer_id", "purpose"]))
            s.commit()

    def consents(self, customer_id: str) -> dict[str, bool]:
        with Session() as s:
            rows = s.execute(
                select(Consent.purpose, Consent.granted).where(
                    Consent.customer_id == customer_id)
            ).all()
        return {p: bool(g) for p, g in rows} or {p: True for p in PURPOSES}

    def set_consent(self, customer_id: str, purpose: str, granted: bool) -> dict[str, bool]:
        with Session() as s:
            stmt = insert(Consent).values(
                customer_id=customer_id, purpose=purpose,
                granted=granted, updated_at=datetime.now(),
            )
            s.execute(stmt.on_conflict_do_update(
                index_elements=["customer_id", "purpose"],
                set_={"granted": granted, "updated_at": datetime.now()},
            ))
            s.commit()
        self.write(customer_id, purpose=purpose, kind="consent_change", shown=None,
                   detail=f"{'granted' if granted else 'withdrawn'} by customer")
        return self.consents(customer_id)

    # ------------------------------------------------------------------ ledger
    def write(self, customer_id: str, purpose: str, kind: str, *, as_of=None,
              product_id: str | None = None, shown: bool | None = None,
              score: float | None = None, suppressed_by: str | None = None,
              reason_codes: list[str] | None = None, features_used: list[str] | None = None,
              detail: str | None = None) -> str:
        eid = uuid.uuid4().hex[:12]
        with Session() as s:
            s.add(LedgerEntry(
                entry_id=eid, ts=datetime.now(), customer_id=customer_id, as_of=as_of,
                purpose=purpose, kind=kind, product_id=product_id, shown=shown,
                score=score, suppressed_by=suppressed_by,
                reason_codes=reason_codes or [], features_used=features_used or [],
                detail=detail,
            ))
            s.commit()
        return eid

    def entries(self, customer_id: str, limit: int = 100) -> list[dict]:
        with Session() as s:
            rows = s.execute(
                select(LedgerEntry)
                .where(LedgerEntry.customer_id == customer_id)
                .order_by(LedgerEntry.ts.desc())
                .limit(limit)
            ).scalars().all()

        out = []
        for r in rows:
            out.append({
                "entry_id": r.entry_id,
                "ts": r.ts.strftime("%Y-%m-%d %H:%M") if r.ts else None,
                "customer_id": r.customer_id,
                "as_of": str(r.as_of) if r.as_of else None,
                "purpose": r.purpose,
                "kind": r.kind,
                "product_id": r.product_id,
                "shown": r.shown,
                "score": r.score,
                "suppressed_by": r.suppressed_by,
                "reason_codes": r.reason_codes or [],
                "features_used": r.features_used or [],
                "detail": r.detail,
            })
        return out

    def counts(self) -> dict:
        with Session() as s:
            shown, held = s.execute(
                select(
                    func.count().filter(LedgerEntry.shown.is_(True)),
                    func.count().filter(LedgerEntry.shown.is_(False)),
                ).where(LedgerEntry.kind == "recommendation")
            ).one()
        return {"offers_shown": int(shown or 0), "offers_held_back": int(held or 0)}
