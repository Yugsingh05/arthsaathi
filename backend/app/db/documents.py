"""The small JSON blobs the app used to read off disk.

`demo_checkpoints` and `cases` are configuration-shaped rather than tabular, so
they live in one `documents` table as JSONB instead of being spread over
columns. Corporate exposures are the same idea with a row per exposure.
"""
from __future__ import annotations

from sqlalchemy import select

from app.db.models import Document, Exposure
from app.db.session import Session


def load_document(name: str, default=None):
    with Session() as s:
        row = s.execute(select(Document.payload).where(Document.name == name)).scalar_one_or_none()
    return row if row is not None else default


def load_exposures() -> list[dict]:
    with Session() as s:
        rows = s.execute(select(Exposure.payload).order_by(Exposure.exposure_id)).scalars().all()
    return list(rows)
