"""Runtime configuration, read from the environment.

The only thing this project genuinely needs from the outside is a Postgres
URL. On a developer machine it comes from backend/.env; in a container it is
injected by compose. Nothing else is read from disk at runtime.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# Loading .env is a no-op when the file is absent, which is the container case:
# there the variables are already in the environment.
load_dotenv(BACKEND_ROOT / ".env")


def _normalise(url: str) -> str:
    """Point SQLAlchemy at psycopg 3 and strip libpq-only query parameters.

    Neon hands out `postgresql://...`, which SQLAlchemy maps to psycopg 2.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@lru_cache
def database_url() -> str:
    """The pooled URL, used for everything the API does while serving."""
    url = os.getenv("DATABASE_URL", "").strip().strip('"').strip("'")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Put it in backend/.env (see .env.example) "
            "or pass it into the container."
        )
    return _normalise(url)


@lru_cache
def bulk_database_url() -> str:
    """The direct URL, used for seeding.

    Neon's pooled endpoint sits behind pgbouncer, which drops a connection part
    way through a large COPY. The unpooled endpoint is the same database with
    `-pooler` removed from the host; DATABASE_URL_UNPOOLED overrides it.
    """
    explicit = os.getenv("DATABASE_URL_UNPOOLED", "").strip().strip('"').strip("'")
    if explicit:
        return _normalise(explicit)
    return database_url().replace("-pooler", "", 1)
