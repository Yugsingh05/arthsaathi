"""COPY-based bulk transfer between Postgres and pandas.

The feature engine works on whole tables, so row-by-row SELECT is the wrong
shape: 525k transactions through the ORM is minutes, the same rows through
COPY is seconds. Everything heavy goes through here.
"""
from __future__ import annotations

import io
from collections.abc import Iterable

import pandas as pd
from sqlalchemy import Engine, text

# Neon's pooler drops a connection part way through a very large COPY, and the
# direct endpoint is not much happier. Chunking keeps every statement short.
WRITE_CHUNK_ROWS = 25_000


def _raw(conn):
    """The psycopg connection underneath a SQLAlchemy one."""
    return conn.connection.driver_connection


def read_frame(
    engine: Engine,
    sql: str,
    *,
    parse_dates: Iterable[str] = (),
    bool_columns: Iterable[str] = (),
) -> pd.DataFrame:
    """Run a query and return it as a DataFrame, over the COPY protocol.

    COPY renders booleans as the literals t/f, which pandas reads as strings —
    `bool_columns` names the ones to convert back.
    """
    buf = io.BytesIO()
    with engine.connect() as conn:
        raw = _raw(conn)
        with raw.cursor() as cur, cur.copy(
            f"COPY ({sql}) TO STDOUT WITH (FORMAT csv, HEADER true)"
        ) as copy:
            for block in copy:
                buf.write(block)
    buf.seek(0)
    if buf.getbuffer().nbytes == 0:
        return pd.DataFrame()
    df = pd.read_csv(buf, parse_dates=list(parse_dates))
    for col in bool_columns:
        if col in df.columns:
            df[col] = df[col].map({"t": True, "f": False, True: True, False: False})
    return df


def write_frame(
    engine: Engine,
    df: pd.DataFrame,
    table: str,
    *,
    columns: list[str] | None = None,
    truncate: bool = True,
) -> int:
    """Replace a table's contents with a DataFrame. Returns rows written."""
    cols = columns or list(df.columns)
    collist = ", ".join(f'"{c}"' for c in cols)
    written = 0

    with engine.begin() as conn:
        if truncate:
            conn.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))

    for start in range(0, len(df), WRITE_CHUNK_ROWS):
        chunk = df.iloc[start : start + WRITE_CHUNK_ROWS]
        buf = io.StringIO()
        chunk.to_csv(buf, index=False, header=False, columns=cols)
        payload = buf.getvalue()
        # a fresh transaction per chunk, so a dropped socket costs one chunk
        with engine.begin() as conn:
            raw = _raw(conn)
            with raw.cursor() as cur, cur.copy(
                f'COPY "{table}" ({collist}) FROM STDIN WITH (FORMAT csv)'
            ) as copy:
                copy.write(payload)
        written += len(chunk)

    return written


def table_count(engine: Engine, table: str) -> int:
    with engine.connect() as conn:
        return int(conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar_one())
