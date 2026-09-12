from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session as SASession
from sqlalchemy.orm import sessionmaker

from app.core.config import bulk_database_url, database_url

# pool_pre_ping matters on Neon: an idle compute suspends and the pooled
# connection you are holding goes dead without telling you. pre_ping turns that
# into one wasted round trip instead of a 500.
engine: Engine = create_engine(
    database_url(),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=300,
)

Session = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[SASession]:
    s = Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def bulk_engine() -> Engine:
    """A short-lived engine on the direct endpoint, for COPY-sized work."""
    return create_engine(bulk_database_url(), poolclass=None, pool_pre_ping=True)
