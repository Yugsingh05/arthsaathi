from __future__ import annotations

import json
import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

SEED = 20260912
RNG = np.random.default_rng(SEED)
fake = Faker("en_IN")
Faker.seed(SEED)

DATA = Path(__file__).resolve().parents[2] / "data"
TODAY = date(2026, 9, 12)
START = TODAY - timedelta(days=365)

T1 = TODAY - timedelta(days=70)
T2 = TODAY - timedelta(days=21)
T3 = TODAY

BANK_CODES = ["SBIN", "HDFC", "ICIC", "UTIB", "KKBK", "BARB", "PUNB", "YESB", "IDFB"]
UPI_HANDLES = ["okaxis", "oksbi", "okhdfcbank", "okicici", "ybl", "paytm", "ibl", "apl"]

MERCHANTS = {
    "groceries": ["DMART", "RELIANCE FRESH", "APNA KIRANA STORE", "MORE SUPERMARKET", "STAR BAZAAR"],
    "food_delivery": ["SWIGGY", "ZOMATO"],
    "fuel": ["HP PETROL PUMP", "INDIAN OIL", "BHARAT PETROLEUM"],
    "utilities": ["PGVCL", "TORRENT POWER", "GUJARAT GAS", "MGVCL"],
    "mobile_recharge": ["JIO RECHARGE", "AIRTEL PREPAID", "VI RECHARGE"],
    "ecommerce": ["AMAZON", "FLIPKART", "MEESHO"],
    "medical": ["APOLLO PHARMACY", "MEDPLUS", "CIVIL HOSPITAL"],
    "transport": ["UBER", "OLA", "GSRTC", "IRCTC"],
    "apparel": ["MAX FASHION", "V MART", "BIG BAZAAR"],
    "entertainment": ["HOTSTAR", "NETFLIX", "INOX"],
    "education": ["SCHOOL FEES", "TUITION CLASSES"],
}

CITIES = [
    ("Rajkot", "Gujarat", "gu"), ("Bhavnagar", "Gujarat", "gu"), ("Ahmedabad", "Gujarat", "gu"),
    ("Surat", "Gujarat", "gu"), ("Junagadh", "Gujarat", "gu"), ("Jamnagar", "Gujarat", "gu"),
    ("Indore", "Madhya Pradesh", "hi"), ("Jaipur", "Rajasthan", "hi"), ("Kanpur", "Uttar Pradesh", "hi"),
    ("Patna", "Bihar", "hi"), ("Nagpur", "Maharashtra", "hi"), ("Ranchi", "Jharkhand", "hi"),
]

PERSONAS = {
    "gig_worker": dict(
        label="Gig delivery partner", income_style="weekly_variable", base=4200,
        cash_share=0.16, emi_count=(0, 2), saver=0.45, occupation="Delivery partner"),
    "salaried_clerk": dict(
        label="Salaried clerk", income_style="monthly_salary", base=32000,
        cash_share=0.20, emi_count=(1, 3), saver=0.70, occupation="Clerk"),
    "kirana_merchant": dict(
        label="Kirana store owner", income_style="daily_merchant", base=2600,
        cash_share=0.28, emi_count=(0, 2), saver=0.55, occupation="Shopkeeper"),
    "seasonal_farmer": dict(
        label="Seasonal farmer", income_style="seasonal_agri", base=95000,
        cash_share=0.42, emi_count=(0, 2), saver=0.35, occupation="Farmer"),
    "daily_wager": dict(
        label="Daily wage worker", income_style="daily_wage_cash", base=620,
        cash_share=0.55, emi_count=(0, 1), saver=0.20, occupation="Labourer"),
    "first_job": dict(
        label="First-job earner", income_style="monthly_salary_junior", base=19500,
        cash_share=0.18, emi_count=(0, 1), saver=0.50, occupation="Trainee"),
    "homemaker_saver": dict(
        label="Homemaker saver", income_style="transfer_dependent", base=14000,
        cash_share=0.30, emi_count=(0, 1), saver=0.80, occupation="Homemaker"),
    "small_contractor": dict(
        label="Small contractor", income_style="lumpy_contract", base=58000,
        cash_share=0.33, emi_count=(1, 3), saver=0.40, occupation="Contractor"),
}

PRODUCTS = [
    ("rd_2000", "deposit", "Recurring Deposit", 0.92, False),
    ("sip_1000", "investment", "Monthly SIP", 0.86, False),
    ("sweep_fd", "deposit", "Savings Sweep FD", 0.80, False),
    ("health_cover", "insurance", "Health Cover", 0.84, False),
    ("accident_cover", "insurance", "Accident Cover", 0.78, False),
    ("kcc", "credit", "Kisan Credit Card", 0.62, True),
    ("gold_loan", "credit", "Gold Loan", 0.55, True),
    ("two_wheeler_loan", "credit", "Two-Wheeler Loan", 0.48, True),
    ("personal_loan", "credit", "Personal Loan", 0.34, True),
    ("top_up_loan", "credit", "Top-up Loan", 0.30, True),
    ("credit_card", "credit", "Credit Card", 0.28, True),
]


def monthly_income_est(style: str, base: float) -> float:
    return {
        "monthly_salary": base,
        "monthly_salary_junior": base,
        "transfer_dependent": base,
        "weekly_variable": base * 4.33,
        "daily_merchant": base * 12.5 * 30 * 0.35,
        "seasonal_agri": base * 0.18,
        "daily_wage_cash": base * 2.0 * 0.55 * 30,
        "lumpy_contract": base * 1.68,
    }[style]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())[:12] or "payee"


def upi(direction: str, counterparty: str, note: str = "Payment") -> str:
    dr = "DR" if direction == "debit" else "CR"
    ref = int(RNG.integers(10**11, 10**12))
    handle = f"{slug(counterparty)}@{RNG.choice(UPI_HANDLES)}"
    return f"UPI/{dr}/{ref}/{counterparty.upper()}/{RNG.choice(BANK_CODES)}/{handle}/{note}"


def rows_to_txn(cid, d, amount, direction, rail, narration, category, merchant=None, hour=None):
    return dict(
        customer_id=cid, txn_date=d, hour=int(hour if hour is not None else RNG.integers(7, 22)),
        amount=round(float(amount), 2), direction=direction, rail=rail,
        narration=narration, category=category, merchant=merchant)


def month_days(d: date) -> int:
    nxt = date(d.year + (d.month == 12), 1 if d.month == 12 else d.month + 1, 1)
    return (nxt - date(d.year, d.month, 1)).days


def make_customers(n: int) -> pd.DataFrame:
    rows = [
        dict(customer_id="CUST0001", name="Kiran Parmar", persona="gig_worker", age=27,
             city="Rajkot", state="Gujarat", language="gu", gender="M"),
        dict(customer_id="CUST0002", name="Meena Solanki", persona="salaried_clerk", age=34,
             city="Bhavnagar", state="Gujarat", language="hi", gender="F"),
        dict(customer_id="CUST0003", name="Rafiq Shaikh", persona="kirana_merchant", age=41,
             city="Ahmedabad", state="Gujarat", language="gu", gender="M"),
        dict(customer_id="CUST0004", name="Devang Trivedi", persona="small_contractor", age=38,
             city="Surat", state="Gujarat", language="gu", gender="M", pattern="disbursal_sweep"),
        dict(customer_id="CUST0005", name="Shabana Qureshi", persona="kirana_merchant", age=35,
             city="Jaipur", state="Rajasthan", language="hi", gender="F", pattern="circular"),
        dict(customer_id="CUST0006", name="Harpreet Kaur", persona="salaried_clerk", age=44,
             city="Kanpur", state="Uttar Pradesh", language="hi", gender="F", pattern="repeat_restructure"),
        dict(customer_id="CUST0007", name="Mohan Rathod", persona="daily_wager", age=49,
             city="Indore", state="Madhya Pradesh", language="hi", gender="M", pattern="emi_burden"),
        dict(customer_id="CUST0008", name="Farida Sheikh", persona="first_job", age=26,
             city="Ahmedabad", state="Gujarat", language="gu", gender="F", pattern="unsecured_ramp"),
    ]
    keys = list(PERSONAS)
    for i in range(9, n + 1):
        persona = str(RNG.choice(keys, p=[0.16, 0.20, 0.14, 0.10, 0.12, 0.11, 0.09, 0.08]))
        city, state, lang = CITIES[int(RNG.integers(0, len(CITIES)))]
        gender = "F" if RNG.random() < 0.44 else "M"
        rows.append(dict(
            customer_id=f"CUST{i:04d}",
            name=fake.name_female() if gender == "F" else fake.name_male(),
            persona=persona, age=int(RNG.integers(21, 62)),
            city=city, state=state, language=lang if RNG.random() < 0.85 else "en", gender=gender))

    df = pd.DataFrame(rows)
    if "pattern" not in df.columns:
        df["pattern"] = None
    df["pattern"] = df["pattern"].astype("object")
    df["occupation"] = df.persona.map(lambda p: PERSONAS[p]["occupation"])
    df["persona_label"] = df.persona.map(lambda p: PERSONAS[p]["label"])
    df["account_opened"] = [START - timedelta(days=int(RNG.integers(200, 3200))) for _ in range(len(df))]
    df["kyc_level"] = np.where(RNG.random(len(df)) < 0.78, "full", "min")
    df["smartphone"] = RNG.random(len(df)) < 0.88
    df["consent_personalisation"] = True
    df["consent_stress_watch"] = RNG.random(len(df)) < 0.95
    df["consent_fraud_watch"] = True
    df.loc[df.customer_id.isin(["CUST0001", "CUST0002", "CUST0003"]), ["consent_stress_watch"]] = True
    return df


def simulate(cust: dict) -> tuple[list[dict], list[dict], list[dict]]:
    cid = cust["customer_id"]
    p = PERSONAS[cust["persona"]]
    style, base = p["income_style"], p["base"]
    raw = cust.get("pattern")
    pattern = None if raw is None or (isinstance(raw, float) and np.isnan(raw)) else str(raw)
    demo = cid in ("CUST0001", "CUST0002", "CUST0003") or pattern is not None

    txns: list[dict] = []
    events: list[dict] = []

    scale = 1.0 if demo else float(np.clip(RNG.normal(1.0, 0.22), 0.5, 1.9))
    if cid == "CUST0002":
        salary = 32000.0
    elif cid == "CUST0003":
        salary = base
    else:
        salary = base * scale

    emis: list[dict] = []
    lo, hi = p["emi_count"]
    n_emi = 2 if cid == "CUST0002" else (1 if cid == "CUST0001" else
                                         (1 if pattern == "emi_burden" else
                                          3 if pattern == "unsecured_ramp" else
                                          int(RNG.integers(lo, hi + 1))))
    emi_catalog = [("two_wheeler_loan", 0.9), ("personal_loan", 1.6), ("gold_loan", 1.1),
                   ("home_loan", 4.5), ("consumer_durable", 0.5)]
    for k in range(n_emi):
        kind, mult = emi_catalog[int(RNG.integers(0, len(emi_catalog)))]
        monthly = salary if style in ("monthly_salary", "monthly_salary_junior", "transfer_dependent") \
            else salary * (4.3 if style == "weekly_variable" else 26 if style == "daily_merchant" else 1.0)
        amt = round(monthly * float(np.clip(RNG.normal(0.13, 0.05), 0.04, 0.30)), -1)
        if cid == "CUST0002":
            amt = [7400.0, 4760.0][k]
            kind = ["home_loan", "two_wheeler_loan"][k]
        if cid == "CUST0001":
            amt, kind = 2450.0, "two_wheeler_loan"
        if pattern == "emi_burden":
            amt, kind = 6200.0, "gold_loan"
        if pattern == "unsecured_ramp":
            amt, kind = [3100.0, 2400.0, 1900.0][min(k, 2)], "consumer_durable"
        due_day = [5, 3, 7, 4, 9, 6, 2, 8][(int(cid[-2:]) - 1) % 8] if demo else int(RNG.integers(2, 11))
        emis.append(dict(
            customer_id=cid, loan_id=f"{cid}-L{k+1}", product=kind, emi_amount=float(amt),
            due_day=due_day, tenure_months=int(RNG.choice([12, 24, 36, 48, 60])),
            outstanding=float(round(amt * RNG.integers(8, 40), -2)),
            interest_rate=float(round(RNG.uniform(9.5, 16.5), 2))))

    is_saver = RNG.random() < p["saver"]
    save_amt = 0.0
    if cid == "CUST0001":
        is_saver, save_amt = True, 3000.0
    elif cid == "CUST0002":
        is_saver, save_amt = True, 2000.0
    elif is_saver:
        save_amt = round(max(300, salary * float(np.clip(RNG.normal(0.09, 0.04), 0.02, 0.2))), -2)

    def kiran_weekly(day: date) -> float:
        if day > TODAY - timedelta(days=30):
            return 2100.0
        if day > TODAY - timedelta(days=51):
            return 2800.0
        return 4200.0

    drop_from = TODAY - timedelta(days=51)
    missed_emi_month = (TODAY - timedelta(days=24)).month

    mi = monthly_income_est(style, salary)
    emi_total = sum(e["emi_amount"] for e in emis)
    rent_m = 0.0 if cust["persona"] == "seasonal_farmer" else mi * 0.155
    bills_m = mi * 0.028 + 300
    target_save = 0.12 if is_saver else -0.05
    consumption = mi * (1 - target_save)
    cash_budget = consumption * p["cash_share"]
    disc_budget = max(mi * 0.05, consumption - emi_total - rent_m - bills_m - cash_budget)
    DISC_MIX = {"groceries": 0.39, "food_delivery": 0.09, "fuel": 0.16, "transport": 0.08,
                "ecommerce": 0.10, "medical": 0.06, "apparel": 0.06, "entertainment": 0.06}

    d = START
    while d <= TODAY:
        dow, dom = d.weekday(), d.day

        if style == "monthly_salary" or style == "monthly_salary_junior":
            if dom == 1:
                late = RNG.random() < (0.06 if cid == "CUST0002" else 0.18)
                pay_d = d + timedelta(days=int(RNG.integers(1, 5))) if late else d
                if pay_d <= TODAY:
                    amt = salary * float(np.clip(RNG.normal(1.0, 0.02), 0.9, 1.1))
                    emp = "ACME TEXTILES PVT LTD" if cid == "CUST0002" else fake.company().upper()[:26]
                    txns.append(rows_to_txn(cid, pay_d, amt, "credit", "NEFT",
                                f"NEFT-CITIN{int(RNG.integers(10**7, 10**8))}-{emp}-SALARY {d:%b%y}".upper(),
                                "salary", emp, hour=int(RNG.integers(9, 19))))
        elif style == "weekly_variable":
            if dow == 0:
                wk = kiran_weekly(d) if cid == "CUST0001" else salary
                amt = wk * float(np.clip(RNG.normal(1.0, 0.11 if demo else 0.26), 0.45, 1.8))
                txns.append(rows_to_txn(cid, d, amt, "credit", "UPI",
                            upi("credit", "ZOMATO PAYOUTS" if RNG.random() < .5 else "SWIGGY PARTNER", "Weekly payout"),
                            "gig_income", "GIG PLATFORM", hour=int(RNG.integers(18, 23))))
        elif style == "daily_merchant":
            for _ in range(int(RNG.integers(6, 19))):
                amt = float(np.clip(RNG.lognormal(4.6, 0.8), 20, 4200))
                txns.append(rows_to_txn(cid, d, amt, "credit", "UPI",
                            upi("credit", fake.first_name().upper() + " " + fake.last_name().upper(), "Soundbox"),
                            "business_income", "SOUNDBOX", hour=int(RNG.integers(8, 22))))
        elif style == "seasonal_agri":
            if d.month in (3, 4, 10, 11) and dom in (12, 24):
                amt = salary * float(np.clip(RNG.normal(0.55, 0.2), 0.15, 1.1))
                txns.append(rows_to_txn(cid, d, amt, "credit", "NEFT",
                            f"NEFT-APMC {cust['city'].upper()}-CROP SALE-{int(RNG.integers(10**5, 10**6))}",
                            "business_income", "APMC MANDI"))
        elif style == "daily_wage_cash":
            if dow != 6 and RNG.random() < 0.55:
                decay = 1.0
                if pattern == "emi_burden":
                    decay = float(np.clip(1.0 - (d - START).days / 365 * 0.45, 0.5, 1.0))
                amt = salary * decay * float(np.clip(RNG.normal(1.0, 0.3), 0.4, 2.0)) * RNG.integers(1, 4)
                txns.append(rows_to_txn(cid, d, amt, "credit", "CASH",
                            f"BY CASH-{cust['city'].upper()} BR", "cash_deposit"))
        elif style == "transfer_dependent":
            if dom == 3:
                txns.append(rows_to_txn(cid, d, salary * float(np.clip(RNG.normal(1, .08), .7, 1.3)),
                            "credit", "IMPS",
                            f"IMPS/P2A/{int(RNG.integers(10**11, 10**12))}/{fake.last_name().upper()}/{RNG.choice(BANK_CODES)}",
                            "transfer_in"))
        elif style == "lumpy_contract":
            if RNG.random() < 0.07:
                txns.append(rows_to_txn(cid, d, salary * float(np.clip(RNG.normal(0.8, 0.45), 0.2, 2.4)),
                            "credit", "RTGS",
                            f"RTGS-{fake.company().upper()[:22]}-BILL {int(RNG.integers(1000,9999))}",
                            "business_income"))

        for e in emis:
            if dom == e["due_day"]:
                missed = cid == "CUST0001" and d.month == missed_emi_month and d.year == TODAY.year
                if not missed and (demo or RNG.random() > 0.06):
                    txns.append(rows_to_txn(cid, d, e["emi_amount"], "debit", "ACH",
                                f"ACH-D-{e['product'].replace('_',' ').upper()} EMI-{e['loan_id'][-4:]}",
                                "emi", hour=int(RNG.integers(6, 10))))
                else:
                    txns.append(rows_to_txn(cid, d, 0.0, "debit", "ACH",
                                f"ACH-RETURN-{e['product'].replace('_',' ').upper()} EMI-INSUFFICIENT FUNDS",
                                "emi_bounce", hour=8))
                    events.append(dict(customer_id=cid, event_date=d, event="emi_missed",
                                       detail=e["loan_id"]))

        if dom == 4 and cust["persona"] != "seasonal_farmer":
            txns.append(rows_to_txn(cid, d, round(rent_m, -2), "debit", "UPI",
                        upi("debit", "LANDLORD " + fake.last_name().upper(), "Rent"), "rent"))
        if dom == 9:
            m = str(RNG.choice(MERCHANTS["utilities"]))
            txns.append(rows_to_txn(cid, d, float(np.clip(RNG.normal(mi * 0.028, mi * 0.008), 180, 3200)),
                        "debit", "UPI", upi("debit", m, "Bill"), "utilities", m))
        if dom == 14:
            m = str(RNG.choice(MERCHANTS["mobile_recharge"]))
            txns.append(rows_to_txn(cid, d, float(RNG.choice([199, 239, 299, 349, 399, 666])),
                        "debit", "UPI", upi("debit", m, "Recharge"), "mobile_recharge", m))
        for cat, prob in [("groceries", 0.34), ("food_delivery", 0.14), ("fuel", 0.16),
                          ("transport", 0.13), ("ecommerce", 0.07), ("medical", 0.04),
                          ("apparel", 0.03), ("entertainment", 0.05)]:
            if RNG.random() < prob:
                m = str(RNG.choice(MERCHANTS[cat]))
                amt = (disc_budget * DISC_MIX[cat] / 30 / prob) * float(np.clip(RNG.lognormal(0, 0.5), 0.25, 3))
                rail = "POS" if RNG.random() < 0.2 else "UPI"
                narr = (f"POS {int(RNG.integers(4000,4999))}XXXX{int(RNG.integers(1000,9999))} {m} {cust['city'].upper()}"
                        if rail == "POS" else upi("debit", m, "Payment"))
                txns.append(rows_to_txn(cid, d, max(20.0, amt), "debit", rail, narr, cat, m))

        if RNG.random() < 0.12:
            amt = float(np.clip(round(cash_budget / 30 / 0.12 / 500) * 500, 500, 20000))
            txns.append(rows_to_txn(cid, d, amt, "debit", "ATM",
                        f"ATW-{int(RNG.integers(4000,4999))}XXXXXXXX{int(RNG.integers(1000,9999))}-{cust['city'].upper()} MAIN BR",
                        "cash_withdrawal"))

        if is_saver and dom == 22:
            stressed = cid == "CUST0001" and d >= drop_from
            if not stressed:
                txns.append(rows_to_txn(cid, d, save_amt, "debit", "IMPS",
                            f"IMPS/P2A/{int(RNG.integers(10**11,10**12))}/SELF SAVINGS/{RNG.choice(BANK_CODES)}",
                            "savings_transfer"))

        d += timedelta(days=1)

    if pattern == "disbursal_sweep":
        d0 = TODAY - timedelta(days=40)
        txns.append(rows_to_txn(cid, d0, 300000, "credit", "NEFT",
                    f"NEFT-LOANDISB-PERSONAL LOAN DISBURSAL-{int(RNG.integers(10**5, 10**6))}",
                    "loan_disbursal", hour=11))
        for k, amt in enumerate([95000, 80000, 62000, 41000]):
            payee = fake.name().upper()
            txns.append(rows_to_txn(cid, d0 + timedelta(days=1 + k // 2), amt, "debit", "IMPS",
                        f"IMPS/P2A/{int(RNG.integers(10**11, 10**12))}/{payee}/{RNG.choice(BANK_CODES)}",
                        "p2p_out", payee, hour=int(RNG.integers(10, 20))))
        events.append(dict(customer_id=cid, event_date=d0, event="disbursal_sweep",
                           detail="Rs 2,78,000 of a Rs 3,00,000 disbursal left within 48 hours"))

    if pattern == "circular":
        ring = [fake.name().upper() for _ in range(5)]
        d0 = TODAY - timedelta(days=62)
        for rnd in range(4):
            base = d0 + timedelta(days=rnd * 14)
            amt = float(round(RNG.uniform(45000, 85000), -3))
            for k, party in enumerate(ring):
                day = base + timedelta(days=k // 2)
                if day > TODAY:
                    continue
                for direction in ("credit", "debit"):
                    txns.append(rows_to_txn(
                        cid, day, amt * float(np.clip(RNG.normal(1, .04), .9, 1.1)),
                        direction, "IMPS",
                        f"IMPS/P2A/{int(RNG.integers(10**11, 10**12))}/{party}/{RNG.choice(BANK_CODES)}",
                        "transfer_in" if direction == "credit" else "p2p_out", party,
                        hour=int(RNG.integers(9, 22))))
        events.append(dict(customer_id=cid, event_date=d0, event="circular_transfers",
                           detail="Funds cycling between the same five counterparties"))

    if pattern == "repeat_restructure":
        for offset in (150, 60):
            d0 = TODAY - timedelta(days=offset)
            txns.append(rows_to_txn(cid, d0, 0.0, "debit", "ACH",
                        "ACH-DEFERRED-EMI MORATORIUM APPROVED", "emi_deferral", hour=8))
            events.append(dict(customer_id=cid, event_date=d0, event="emi_deferral",
                               detail="EMI deferred by one month"))

    if pattern == "unsecured_ramp":
        for k2 in range(4):
            d0 = TODAY - timedelta(days=170 - k2 * 45)
            txns.append(rows_to_txn(cid, d0, 40000 + k2 * 15000, "credit", "NEFT",
                        f"NEFT-LOANDISB-CONSUMER LOAN DISBURSAL-{int(RNG.integers(10**5, 10**6))}",
                        "loan_disbursal", hour=12))
        events.append(dict(customer_id=cid, event_date=TODAY - timedelta(days=170),
                           event="unsecured_ramp", detail="Four consumer loans drawn in six months"))

    if cust["persona"] == "first_job":
        events.append(dict(customer_id=cid, event_date=START + timedelta(days=40),
                           event="first_salary", detail="first salary credit"))
    for e in emis:
        events.append(dict(customer_id=cid, event_date=START + timedelta(days=int(RNG.integers(5, 200))),
                           event="new_emi", detail=e["loan_id"]))

    if not demo and RNG.random() < 0.18:
        s0 = TODAY - timedelta(days=int(RNG.integers(20, 80)))
        txns = [t for t in txns if not (t["txn_date"] >= s0 and t["category"] in
                ("salary", "gig_income", "business_income") and RNG.random() < 0.45)]
        events.append(dict(customer_id=cid, event_date=s0, event="income_shock", detail="inflow drop"))

    if cid == "CUST0001" or (not demo and RNG.random() < 0.06):
        fd = TODAY - timedelta(days=2) if cid == "CUST0001" else TODAY - timedelta(days=int(RNG.integers(1, 45)))
        amounts = [9000, 12000, 9500, 7500] if cid == "CUST0001" else \
            [float(round(RNG.uniform(4000, 18000), -2)) for _ in range(int(RNG.integers(3, 6)))]
        for a in amounts:
            payee = fake.name().upper()
            txns.append(rows_to_txn(cid, fd, a, "debit", "IMPS",
                        f"IMPS/P2A/{int(RNG.integers(10**11,10**12))}/{payee}/{RNG.choice(BANK_CODES)}",
                        "p2p_out", payee, hour=2))
        events.append(dict(customer_id=cid, event_date=fd, event="fraud_episode",
                           detail=f"{len(amounts)} transfers, Rs {int(sum(amounts)):,}"))

    return txns, emis, events


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    customers = make_customers(500)

    all_txns: list[dict] = []
    all_emis: list[dict] = []
    all_events: list[dict] = []
    for rec in customers.to_dict("records"):
        t, e, ev = simulate(rec)
        all_txns += t
        all_emis += e
        all_events += ev

    txns = pd.DataFrame(all_txns).sort_values(["customer_id", "txn_date", "hour"]).reset_index(drop=True)
    txns["txn_id"] = [f"T{i:08d}" for i in range(len(txns))]
    txns["txn_date"] = pd.to_datetime(txns.txn_date)
    opening = {c: float(RNG.uniform(1500, 40000)) for c in customers.customer_id}
    signed = np.where(txns.direction.eq("credit"), txns.amount, -txns.amount)
    txns["balance_after"] = (
        pd.Series(signed).groupby(txns.customer_id).cumsum()
        + txns.customer_id.map(opening)).round(2)

    emis = pd.DataFrame(all_emis)
    events = pd.DataFrame(all_events)
    events["event_date"] = pd.to_datetime(events.event_date)
    products = pd.DataFrame(PRODUCTS, columns=["product_id", "family", "label_en", "benefit_score", "is_credit"])
    customers["account_opened"] = pd.to_datetime(customers.account_opened)

    customers.to_parquet(DATA / "customers.parquet", index=False)
    txns.to_parquet(DATA / "transactions.parquet", index=False)
    emis.to_parquet(DATA / "emis.parquet", index=False)
    events.to_parquet(DATA / "life_events.parquet", index=False)
    products.to_parquet(DATA / "products.parquet", index=False)
    (DATA / "demo_checkpoints.json").write_text(json.dumps({
        "today": str(TODAY),
        "checkpoints": [
            {"key": "t1", "date": str(T1), "label": "Baseline",
             "sub": "No risk signals", "month": T1.strftime("%b %Y")},
            {"key": "t2", "date": str(T2), "label": "Stress detected",
             "sub": "Income down 40%, EMI missed", "month": T2.strftime("%b %Y")},
            {"key": "t3", "date": str(T3), "label": "Fraud alert",
             "sub": "Four transfers at 02:00", "month": T3.strftime("%b %Y")},
        ],
        "demo_customers": ["CUST0001", "CUST0002", "CUST0003",
                           "CUST0004", "CUST0005", "CUST0006", "CUST0007", "CUST0008"],
    }, indent=2))

    print(f"customers      {len(customers):>8,}")
    print(f"transactions   {len(txns):>8,}  ({txns.txn_date.min():%Y-%m-%d} to {txns.txn_date.max():%Y-%m-%d})")
    print(f"emis           {len(emis):>8,}")
    print(f"life events    {len(events):>8,}   " + ", ".join(f"{k}:{v}" for k, v in events.event.value_counts().items()))
    print(f"products       {len(products):>8,}")
    print("\nKiran (CUST0001) weekly gig income, last 12 weeks:")
    k = txns[(txns.customer_id == "CUST0001") & (txns.category == "gig_income")].tail(12)
    print("  " + "  ".join(f"{a:,.0f}" for a in k.amount))


if __name__ == "__main__":
    main()
