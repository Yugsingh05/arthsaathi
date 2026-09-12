"""The whole application schema.

Everything the app reads or writes lives here — the synthetic dataset, the
consent and decision ledger, and the trained model itself. There is no local
parquet, duckdb or joblib file at runtime.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------
# the synthetic dataset: written once by the seeder, read-only thereafter
# --------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str | None] = mapped_column(String(120))
    persona: Mapped[str | None] = mapped_column(String(64))
    age: Mapped[int | None] = mapped_column(Integer)
    city: Mapped[str | None] = mapped_column(String(80))
    state: Mapped[str | None] = mapped_column(String(80))
    language: Mapped[str | None] = mapped_column(String(8))
    gender: Mapped[str | None] = mapped_column(String(16))
    pattern: Mapped[str | None] = mapped_column(String(64))
    occupation: Mapped[str | None] = mapped_column(String(80))
    persona_label: Mapped[str | None] = mapped_column(String(120))
    account_opened: Mapped[date | None] = mapped_column(Date)
    kyc_level: Mapped[str | None] = mapped_column(String(32))
    smartphone: Mapped[bool | None] = mapped_column(Boolean)
    consent_personalisation: Mapped[bool | None] = mapped_column(Boolean)
    consent_stress_watch: Mapped[bool | None] = mapped_column(Boolean)
    consent_fraud_watch: Mapped[bool | None] = mapped_column(Boolean)


class Transaction(Base):
    __tablename__ = "transactions"

    # the dataset's own txn_id is unique, so it doubles as the key
    txn_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), nullable=False)
    txn_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hour: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[float | None] = mapped_column(Float)
    direction: Mapped[str | None] = mapped_column(String(8))
    rail: Mapped[str | None] = mapped_column(String(16))
    narration: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(48))
    merchant: Mapped[str | None] = mapped_column(String(120))
    balance_after: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        Index("ix_transactions_customer_date", "customer_id", "txn_date"),
    )


class Emi(Base):
    __tablename__ = "emis"

    loan_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    product: Mapped[str | None] = mapped_column(String(64))
    emi_amount: Mapped[float | None] = mapped_column(Float)
    due_day: Mapped[int | None] = mapped_column(Integer)
    tenure_months: Mapped[int | None] = mapped_column(Integer)
    outstanding: Mapped[float | None] = mapped_column(Float)
    interest_rate: Mapped[float | None] = mapped_column(Float)


class LifeEvent(Base):
    __tablename__ = "life_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date)
    event: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[str | None] = mapped_column(Text)


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    family: Mapped[str | None] = mapped_column(String(48))
    label_en: Mapped[str | None] = mapped_column(String(160))
    benefit_score: Mapped[float | None] = mapped_column(Float)
    is_credit: Mapped[bool | None] = mapped_column(Boolean)


class Exposure(Base):
    """Corporate exposures. The two time series stay as JSONB."""

    __tablename__ = "exposures"

    exposure_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class Document(Base):
    """Small JSON documents that used to sit beside the code.

    `demo_checkpoints` and `cases` live here, keyed by name.
    """

    __tablename__ = "documents"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --------------------------------------------------------------------------
# mutable runtime state: was duckdb, now Postgres
# --------------------------------------------------------------------------
class Consent(Base):
    __tablename__ = "consents"

    customer_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(48), primary_key=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LedgerEntry(Base):
    __tablename__ = "ledger"

    entry_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    customer_id: Mapped[str] = mapped_column(String(32), nullable=False)
    as_of: Mapped[date | None] = mapped_column(Date)
    purpose: Mapped[str | None] = mapped_column(String(48))
    kind: Mapped[str | None] = mapped_column(String(48))
    product_id: Mapped[str | None] = mapped_column(String(48))
    shown: Mapped[bool | None] = mapped_column(Boolean)
    score: Mapped[float | None] = mapped_column(Float)
    suppressed_by: Mapped[str | None] = mapped_column(String(64))
    reason_codes: Mapped[list | None] = mapped_column(JSONB, default=list)
    features_used: Mapped[list | None] = mapped_column(JSONB, default=list)
    detail: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_ledger_customer_ts", "customer_id", "ts"),
        Index("ix_ledger_kind_shown", "kind", "shown"),
    )


# --------------------------------------------------------------------------
# the trained model, so a rebuild never retrains
# --------------------------------------------------------------------------
class ModelArtifact(Base):
    """A joblib bundle, keyed by a fingerprint of what produced it.

    The fingerprint covers the training code, the policy rules and the shape of
    the dataset. Boot looks for a row with the current fingerprint: a hit is
    loaded straight out of Postgres, a miss trains once and stores the result
    for every other container, machine and rebuild.
    """

    __tablename__ = "model_artifacts"

    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    blob: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    trained_at: Mapped[str | None] = mapped_column(String(32))
    auc: Mapped[dict | None] = mapped_column(JSONB)
    rows_trained_on: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
