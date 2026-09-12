from __future__ import annotations

import logging
import re
import time
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import Engine

from app.db.bulk import read_frame

log = logging.getLogger(__name__)


RAIL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("UPI",  re.compile(r"^UPI/(?P<dr>DR|CR)/(?P<ref>\d+)/(?P<party>[^/]+)/(?P<bank>[A-Z]{4})/(?P<vpa>[^/]+)/(?P<note>.*)$")),
    ("IMPS", re.compile(r"^IMPS/(?P<mode>P2A|P2P)/(?P<ref>\d+)/(?P<party>[^/]+)/(?P<bank>[A-Z]{4})")),
    ("NEFT", re.compile(r"^NEFT-(?P<ref>[A-Z0-9]+)-(?P<party>.+?)-(?P<note>[A-Z ]+\d*)$")),
    ("RTGS", re.compile(r"^RTGS-(?P<party>.+?)-(?P<note>.+)$")),
    ("ACH",  re.compile(r"^ACH-(?P<kind>D|RETURN)-(?P<party>.+?)(?:-(?P<note>.+))?$")),
    ("ATM",  re.compile(r"^ATW-(?P<card>[0-9X]+)-(?P<party>.+)$")),
    ("POS",  re.compile(r"^POS (?P<card>[0-9X]+) (?P<party>.+)$")),
    ("CASH", re.compile(r"^BY CASH-(?P<party>.+)$")),
]

CATEGORY_RULES: list[tuple[str, re.Pattern]] = [
    ("salary",           re.compile(r"\bSALARY\b|\bSAL \d|PAYROLL")),
    ("gig_income",       re.compile(r"WEEKLY PAYOUT|PAYOUTS|PARTNER")),
    ("business_income",  re.compile(r"SOUNDBOX|APMC|CROP SALE|BILL \d")),
    ("emi_bounce",       re.compile(r"ACH-RETURN|INSUFFICIENT FUNDS|ECS RETURN")),
    ("emi_deferral",     re.compile(r"ACH-DEFERRED|MORATORIUM")),
    ("loan_disbursal",   re.compile(r"LOANDISB|DISBURSAL")),
    ("emi",              re.compile(r"\bEMI\b|LOAN INST|ACH-D-")),
    ("cash_withdrawal",  re.compile(r"^ATW-|\bATM WDL\b|CASH WDL")),
    ("cash_deposit",     re.compile(r"^BY CASH")),
    ("savings_transfer", re.compile(r"SELF SAVINGS|RD INSTALMENT|SIP ")),
    ("rent",             re.compile(r"LANDLORD|\bRENT\b")),
    ("utilities",        re.compile(r"PGVCL|MGVCL|TORRENT POWER|GUJARAT GAS|ELECTRICITY|\bGAS\b")),
    ("mobile_recharge",  re.compile(r"JIO|AIRTEL|\bVI RECHARGE\b|RECHARGE")),
    ("food_delivery",    re.compile(r"SWIGGY|ZOMATO")),
    ("groceries",        re.compile(r"DMART|RELIANCE FRESH|KIRANA|SUPERMARKET|STAR BAZAAR|BIG BAZAAR")),
    ("fuel",             re.compile(r"PETROL|INDIAN OIL|BHARAT PETROLEUM|\bHP \b")),
    ("transport",        re.compile(r"\bUBER\b|\bOLA\b|GSRTC|IRCTC")),
    ("medical",          re.compile(r"APOLLO|MEDPLUS|HOSPITAL|PHARMACY|CLINIC")),
    ("ecommerce",        re.compile(r"AMAZON|FLIPKART|MEESHO")),
    ("apparel",          re.compile(r"MAX FASHION|V MART")),
    ("entertainment",    re.compile(r"HOTSTAR|NETFLIX|INOX|PVR")),
    ("education",        re.compile(r"SCHOOL FEES|TUITION|COLLEGE")),
    ("transfer_in",      re.compile(r"IMPS/P2A/.*")),
]


def parse_narration(narration: str) -> dict:
    text = (narration or "").upper().strip()
    rail, party, vpa, ref = "OTHER", None, None, None
    for name, pat in RAIL_PATTERNS:
        m = pat.match(text)
        if m:
            g = m.groupdict()
            rail = name
            party = (g.get("party") or "").strip() or None
            vpa = g.get("vpa")
            ref = g.get("ref")
            break
    category = "unknown"
    for cat, pat in CATEGORY_RULES:
        if pat.search(text):
            category = cat
            break
    return dict(rail=rail, counterparty=party, vpa=vpa, ref=ref, category=category)


def parse_frame(df: pd.DataFrame) -> pd.DataFrame:
    parsed = pd.DataFrame([parse_narration(n) for n in df.narration], index=df.index)
    out = df.copy()
    out["parsed_rail"] = parsed.rail
    out["parsed_category"] = parsed.category
    out["counterparty"] = parsed.counterparty.fillna(out.get("merchant"))
    return out


BIAS_GUARDED = ["city", "state", "language", "gender", "name", "smartphone", "pin_code", "device"]

FEATURE_COLUMNS = [
    "monthly_income", "salary_regularity", "emi_to_income", "savings_rate", "cash_share",
    "inflow_30d_delta", "digital_share", "avg_balance_30d", "min_balance_30d",
    "balance_volatility", "emi_bounce_90d", "txn_per_month", "distinct_payees_90d",
    "night_txn_share", "new_payee_7d", "large_debit_share", "months_on_book",
    "discretionary_share", "income_volatility", "credit_utilisation_proxy", "age",
    "disbursal_sweep_pct", "restructure_count_365d", "counterparty_recycle", "loan_draws_180d",
]


class FeatureEngine:
    """Holds the dataset in memory for the windowed feature maths.

    Every row comes from Postgres. The transactions table is the expensive one
    — half a million rows — so it is pulled once over COPY at construction and
    the windowing is done in pandas, exactly as before.
    """

    CUSTOMER_BOOLS = ("smartphone", "consent_personalisation",
                      "consent_stress_watch", "consent_fraud_watch")

    def __init__(self, engine: Engine | None = None):
        from app.db.session import engine as default_engine

        self.engine = engine or default_engine
        t0 = time.time()

        self.customers = read_frame(
            self.engine,
            "SELECT * FROM customers ORDER BY customer_id",
            parse_dates=["account_opened"],
            bool_columns=self.CUSTOMER_BOOLS,
        )
        self.txns = read_frame(
            self.engine,
            "SELECT * FROM transactions",
            parse_dates=["txn_date"],
        )
        self.emis = read_frame(self.engine, "SELECT * FROM emis")
        self.events = read_frame(
            self.engine, "SELECT * FROM life_events", parse_dates=["event_date"])
        self.products = read_frame(
            self.engine, "SELECT * FROM products", bool_columns=["is_credit"])

        self.txns = parse_frame(self.txns)
        self._emi_by_cust = self.emis.groupby("customer_id").emi_amount.sum()
        log.info("loaded %s transactions for %s customers from postgres in %.1fs",
                 f"{len(self.txns):,}", len(self.customers), time.time() - t0)

    def _window(self, as_of: date, days: int, offset: int = 0) -> pd.DataFrame:
        hi = pd.Timestamp(as_of) - pd.Timedelta(days=offset)
        lo = hi - pd.Timedelta(days=days)
        t = self.txns
        return t[(t.txn_date > lo) & (t.txn_date <= hi)]

    @staticmethod
    def _sum_by(df: pd.DataFrame, mask: pd.Series) -> pd.Series:
        return df[mask].groupby("customer_id").amount.sum()

    def compute_all(self, as_of: date) -> pd.DataFrame:
        ids = self.customers.customer_id
        idx = pd.Index(ids, name="customer_id")
        z = lambda s: s.reindex(idx).fillna(0.0)

        w365, w90, w30 = self._window(as_of, 365), self._window(as_of, 90), self._window(as_of, 30)
        w30p = self._window(as_of, 30, offset=30)

        credit90 = z(self._sum_by(w90, w90.direction.eq("credit")))
        debit90 = z(self._sum_by(w90, w90.direction.eq("debit")))
        selfsave90 = z(self._sum_by(w90, w90.parsed_category.eq("savings_transfer")))
        consumption90 = (debit90 - selfsave90).clip(lower=0)
        in30 = z(self._sum_by(w30, w30.direction.eq("credit")))
        in30p = z(self._sum_by(w30p, w30p.direction.eq("credit")))

        inc = w365[w365.direction.eq("credit") &
                   w365.parsed_category.isin(["salary", "gig_income", "business_income",
                                              "transfer_in", "cash_deposit"])].copy()
        inc["ym"] = inc.txn_date.dt.to_period("M")
        monthly = inc.groupby(["customer_id", "ym"]).amount.sum()
        monthly_income = z(monthly.groupby("customer_id").tail(3).groupby("customer_id").median())
        income_cv = (monthly.groupby("customer_id").std() /
                     monthly.groupby("customer_id").mean().replace(0, np.nan))
        income_cv = income_cv.reindex(idx).fillna(1.0).clip(0, 1)

        day_spread = inc.groupby("customer_id").apply(
            lambda g: g.txn_date.dt.day.std() if len(g) > 2 else 12.0, include_groups=False)
        day_spread = day_spread.reindex(idx).fillna(12.0).clip(0, 12)
        salary_regularity = (0.55 * (1 - income_cv) + 0.45 * (1 - day_spread / 12)).clip(0, 1)

        emi_amt = z(self._emi_by_cust)
        emi_to_income = (emi_amt / monthly_income.replace(0, np.nan)).fillna(0).clip(0, 3)
        savings_rate = ((credit90 - consumption90) / credit90.replace(0, np.nan)).fillna(0).clip(-1, 1)

        cash90 = z(self._sum_by(w90, w90.parsed_category.isin(["cash_withdrawal", "cash_deposit"])))
        cash_share = (cash90 / debit90.replace(0, np.nan)).fillna(0).clip(0, 1)
        digital_share = 1 - cash_share

        inflow_30d_delta = ((in30 - in30p) / in30p.replace(0, np.nan)).fillna(0).clip(-1, 3)

        bal = w30.sort_values("txn_date").groupby("customer_id").balance_after
        avg_balance_30d = z(bal.mean())
        min_balance_30d = z(bal.min())
        balance_volatility = z(bal.std()) / avg_balance_30d.abs().replace(0, np.nan)
        balance_volatility = balance_volatility.fillna(0).clip(0, 5)

        emi_bounce_90d = z(w90[w90.parsed_category.eq("emi_bounce")].groupby("customer_id").size())
        txn_per_month = z(w90.groupby("customer_id").size()) / 3.0
        distinct_payees_90d = z(w90[w90.direction.eq("debit")].groupby("customer_id").counterparty.nunique())

        night = w90[w90.hour < 5]
        night_txn_share = (z(night.groupby("customer_id").size()) /
                           z(w90.groupby("customer_id").size()).replace(0, np.nan)).fillna(0)

        w7 = self._window(as_of, 7)
        hist = self._window(as_of, 180, offset=7)
        seen = hist[hist.direction.eq("debit")].groupby("customer_id").counterparty.agg(set)
        recent = w7[w7.direction.eq("debit")].groupby("customer_id").counterparty.agg(set)
        new_payee_7d = pd.Series(
            {c: len(v - seen.get(c, set())) for c, v in recent.items()}, dtype="float64")
        new_payee_7d = z(new_payee_7d)

        big = w90[w90.direction.eq("debit") & (w90.amount > 5000)]
        large_debit_share = (z(self._sum_by(big, big.direction.eq("debit"))) /
                             z(self._sum_by(w90, w90.direction.eq("debit"))).replace(0, np.nan)).fillna(0)

        disc = w90[w90.parsed_category.isin(
            ["food_delivery", "ecommerce", "apparel", "entertainment", "transport"])]
        discretionary_share = (z(disc.groupby("customer_id").amount.sum()) /
                               debit90.replace(0, np.nan)).fillna(0)

        age = self.customers.set_index("customer_id").age.reindex(idx).astype(float)
        disb = w90[w90.parsed_category.eq("loan_disbursal") & w90.direction.eq("credit")]
        sweep = {}
        for cid_, g in disb.groupby("customer_id"):
            last = g.sort_values("txn_date").iloc[-1]
            out = w90[(w90.customer_id == cid_) & w90.direction.eq("debit")
                      & (w90.txn_date > last.txn_date)
                      & (w90.txn_date <= last.txn_date + pd.Timedelta(days=7))]
            sweep[cid_] = min(float(out.amount.sum()) / max(float(last.amount), 1.0), 1.0)
        disbursal_sweep_pct = z(pd.Series(sweep, dtype="float64"))

        w365_def = self._window(as_of, 365)
        restructure_count_365d = z(
            w365_def[w365_def.parsed_category.eq("emi_deferral")].groupby("customer_id").size())

        cred_cp = w90[w90.direction.eq("credit")].groupby("customer_id").counterparty.agg(set)
        deb = w90[w90.direction.eq("debit")]
        recycle = {}
        for cid_, g in deb.groupby("customer_id"):
            both = cred_cp.get(cid_, set())
            if not both:
                continue
            back = g[g.counterparty.isin(both)].amount.sum()
            recycle[cid_] = min(float(back) / max(float(g.amount.sum()), 1.0), 1.0)
        counterparty_recycle = z(pd.Series(recycle, dtype="float64"))

        loan_draws_180d = z(self._window(as_of, 180)
                            .pipe(lambda t: t[t.parsed_category.eq("loan_disbursal")])
                            .groupby("customer_id").size())

        opened = pd.to_datetime(self.customers.set_index("customer_id").account_opened).reindex(idx)
        months_on_book = ((pd.Timestamp(as_of) - opened).dt.days / 30.44).fillna(0).clip(0, 240)

        out = pd.DataFrame({
            "monthly_income": monthly_income,
            "salary_regularity": salary_regularity,
            "emi_to_income": emi_to_income,
            "savings_rate": savings_rate,
            "cash_share": cash_share,
            "inflow_30d_delta": inflow_30d_delta,
            "digital_share": digital_share,
            "avg_balance_30d": avg_balance_30d,
            "min_balance_30d": min_balance_30d,
            "balance_volatility": balance_volatility,
            "emi_bounce_90d": emi_bounce_90d,
            "txn_per_month": txn_per_month,
            "distinct_payees_90d": distinct_payees_90d,
            "night_txn_share": night_txn_share,
            "new_payee_7d": new_payee_7d,
            "large_debit_share": large_debit_share,
            "months_on_book": months_on_book,
            "discretionary_share": discretionary_share,
            "income_volatility": income_cv,
            "age": age,
            "disbursal_sweep_pct": disbursal_sweep_pct,
            "restructure_count_365d": restructure_count_365d,
            "counterparty_recycle": counterparty_recycle,
            "loan_draws_180d": loan_draws_180d,
            "credit_utilisation_proxy": (emi_amt * 12 / monthly_income.replace(0, np.nan)).fillna(0).clip(0, 12),
        }, index=idx)
        return out[FEATURE_COLUMNS].replace([np.inf, -np.inf], 0).fillna(0).round(4)

    def compute(self, customer_id: str, as_of: date) -> dict:
        return self.compute_all(as_of).loc[customer_id].to_dict()

    def parser_accuracy(self) -> float:
        return float((self.txns.parsed_category == self.txns.category).mean())
