from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.features import BIAS_GUARDED, FeatureEngine
from app.core.ledger import PURPOSES, Ledger
from app.core.policy import PolicyEngine
from app.i18n.templates import (LANG_NAMES, PRODUCT_BENEFIT, PRODUCT_NAME, REASON_TEMPLATES,
                                UI, inr, t)

CONTRADICTORY: dict[str, set[str]] = {
    "INFLOW_DROP": {"salary_regularity+", "monthly_income+", "income_volatility+"},
    "DISSAVING": {"savings_rate+", "discretionary_share+"},
    "EMI_BURDEN": {"emi_to_income-"},
    "LOW_BALANCE": {"avg_balance_30d+"},
    "CASH_SPIKE": {"digital_share+"},
}


SEGMENT_TR = {
    "hi": {"Steady saver": "नियमित बचतकर्ता", "Spending ahead of income": "आय से ज़्यादा ख़र्च",
           "Stretched borrower": "दबाव में क़र्ज़दार", "Debt-light earner": "कम क़र्ज़ वाला",
           "Cash-first earner": "नक़द-प्रधान", "Fully digital": "पूरी तरह डिजिटल",
           "Variable income": "अस्थिर आय", "Predictable income": "नियमित आय",
           "Balance builder": "बैलेंस बढ़ाने वाला", "Thin balance": "कम बैलेंस",
           "Long-standing customer": "पुराना ग्राहक", "New to the bank": "बैंक में नया",
           "Higher income": "अधिक आय", "Low, irregular income": "कम, अनियमित आय",
           "Lifestyle spender": "शौक़ीन ख़र्चीला", "Essentials only": "सिर्फ़ ज़रूरी ख़र्च",
           "Salaried regular": "नियमित वेतनभोगी", "Irregular earner": "अनियमित कमाई"},
    "gu": {"Steady saver": "નિયમિત બચતકર્તા", "Spending ahead of income": "આવક કરતાં વધુ ખર્ચ",
           "Stretched borrower": "દબાણમાં દેવાદાર", "Debt-light earner": "ઓછા દેવાવાળા",
           "Cash-first earner": "રોકડ-પ્રધાન", "Fully digital": "સંપૂર્ણ ડિજિટલ",
           "Variable income": "અસ્થિર આવક", "Predictable income": "નિયમિત આવક",
           "Balance builder": "બેલેન્સ વધારનાર", "Thin balance": "ઓછું બેલેન્સ",
           "Long-standing customer": "જૂના ગ્રાહક", "New to the bank": "બેંકમાં નવા",
           "Higher income": "વધુ આવક", "Low, irregular income": "ઓછી, અનિયમિત આવક",
           "Lifestyle spender": "શોખીન ખર્ચાળ", "Essentials only": "ફક્ત જરૂરી ખર્ચ",
           "Salaried regular": "નિયમિત પગારદાર", "Irregular earner": "અનિયમિત કમાણી"},
}

OCCUPATION_TR = {
    "hi": {"Delivery partner": "डिलीवरी पार्टनर", "Clerk": "क्लर्क", "Shopkeeper": "दुकानदार",
           "Farmer": "किसान", "Labourer": "मज़दूर", "Trainee": "प्रशिक्षु",
           "Homemaker": "गृहिणी", "Contractor": "ठेकेदार"},
    "gu": {"Delivery partner": "ડિલિવરી પાર્ટનર", "Clerk": "કારકુન", "Shopkeeper": "દુકાનદાર",
           "Farmer": "ખેડૂત", "Labourer": "મજૂર", "Trainee": "તાલીમાર્થી",
           "Homemaker": "ગૃહિણી", "Contractor": "કોન્ટ્રાક્ટર"},
}

CHECKPOINT_TR = {
    "hi": {"Baseline": ("सामान्य", "कोई जोखिम संकेत नहीं"),
           "Stress detected": ("तनाव मिला", "आय 40% घटी, EMI छूटी"),
           "Fraud alert": ("धोखाधड़ी चेतावनी", "रात 02:00 बजे चार ट्रांसफ़र")},
    "gu": {"Baseline": ("સામાન્ય", "કોઈ જોખમ સંકેત નથી"),
           "Stress detected": ("તણાવ મળ્યો", "આવક 40% ઘટી, EMI ચૂકી"),
           "Fraud alert": ("છેતરપિંડી ચેતવણી", "રાત્રે 02:00 વાગ્યે ચાર ટ્રાન્સફર")},
}

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT.parent / "data"


class Engine:
    def __init__(self) -> None:
        self.fe = FeatureEngine(DATA)
        self.policy = PolicyEngine(ROOT / "policies" / "rules.yaml")
        art = joblib.load(ROOT / "models" / "arthsaathi.joblib")
        self.seg = art["segments"]
        self.bank = art["propensity"]
        self.stress = art["stress"]
        self.fraud = art["fraud"]
        self.stress.policy = self.policy
        self.fraud.policy = self.policy
        self.auc = art["auc"]
        from app.core.explain import Explainer
        self.explainer = Explainer(self.bank)
        self.ledger = Ledger(DATA / "arthsaathi.duckdb")
        self.ledger.seed_consents(self.fe.customers)
        self.meta = json.loads((DATA / "demo_checkpoints.json").read_text())
        self.products = self.fe.products.set_index("product_id")
        self._cache: dict[str, pd.DataFrame] = {}
        self._logged: set[tuple[str, str]] = set()

    def features_for(self, as_of: date) -> pd.DataFrame:
        key = str(as_of)
        if key not in self._cache:
            self._cache[key] = self.fe.compute_all(as_of)
        return self._cache[key]

    def customer(self, cid: str) -> dict:
        row = self.fe.customers.set_index("customer_id").loc[cid]
        return {"customer_id": cid, **row.to_dict()}

    def _phrase_ctx(self, cid: str, f: pd.Series, as_of: date) -> dict:
        t_ = self.fe.txns
        saves = t_[(t_.customer_id == cid) & (t_.parsed_category == "savings_transfer")
                   & (t_.txn_date <= pd.Timestamp(as_of))].tail(6)
        save_amt = float(saves.amount.median()) if len(saves) else max(500.0, f.monthly_income * 0.08)
        return dict(
            save_amt=inr(save_amt), income=inr(f.monthly_income), avg_bal=inr(f.avg_balance_30d),
            emi_pct=int(round(f.emi_to_income * 100)), years=int(f.months_on_book // 12),
        )

    def reason_text(self, key: str, lang: str, ctx: dict) -> str:
        tmpl = REASON_TEMPLATES.get(key) or REASON_TEMPLATES.get(key[:-1] + "+")
        if not tmpl:
            return ""
        try:
            return (tmpl.get(lang) or tmpl["en"]).format(**ctx)
        except KeyError:
            return tmpl["en"]

    def decide(self, cid: str, as_of: date, lang: str | None = None) -> dict:
        cust = self.customer(cid)
        lang = lang or cust["language"]
        consents = self.ledger.consents(cid)
        F = self.features_for(as_of)
        f = F.loc[cid]
        x = F.loc[[cid]]

        segment_en = self.seg.name(int(self.seg.predict(x)[0]))
        segment = SEGMENT_TR.get(lang, {}).get(segment_en, segment_en)
        stress = self.stress.score(f.to_dict(), lang) if consents.get("stress_watch", True) else \
            {"score": 0.0, "stressed": False, "fired": [], "rule_score": 0.0, "anomaly": 0.0,
             "threshold": self.policy.rules["stress"]["threshold"], "pause_days": 60,
             "skipped": "stress_watch consent withdrawn"}

        recent = self.fe.txns[(self.fe.txns.customer_id == cid) &
                              (self.fe.txns.txn_date > pd.Timestamp(as_of) - pd.Timedelta(days=7)) &
                              (self.fe.txns.txn_date <= pd.Timestamp(as_of))]
        fraud = self.fraud.score(f.to_dict(), recent, lang) if consents.get("fraud_watch", True) else \
            {"score": 0.0, "suspected": False, "fired": [], "action": "monitor",
             "flagged_transactions": [], "skipped": "fraud_watch consent withdrawn"}

        result = dict(
            customer={**{k: v for k, v in cust.items() if k != "account_opened"},
                      "occupation": OCCUPATION_TR.get(lang, {}).get(
                          cust["occupation"], cust["occupation"])},
            language=lang, language_name=LANG_NAMES.get(lang, lang), as_of=str(as_of),
            segment=segment, consents=consents, purposes=PURPOSES,
            features=self._public_features(f, lang), stress=stress, fraud=fraud,
            ui={k: t(UI, k, lang) for k in UI},
        )

        if not consents.get("personalisation", True):
            result["recommendations"] = []
            result["held_back"] = []
            result["personalisation_off"] = True
            return result

        probs = self.bank.predict_proba(x).iloc[0]
        ctx = {**f.to_dict(), "occupation": cust["occupation"]}
        candidates = []
        for pid, p in probs.items():
            prod = self.products.loc[pid]
            candidates.append(dict(product_id=pid, propensity=float(p),
                                   benefit=float(prod.benefit_score), is_credit=bool(prod.is_credit)))
        decisions = self.policy.apply(candidates, ctx, stressed=bool(stress["stressed"]))

        banned: set[str] = set()
        for fired in stress.get("fired", []):
            banned |= CONTRADICTORY.get(fired["code"], set())
        phrase = self._phrase_ctx(cid, f, as_of)
        shown, held = [], []
        used_keys: set[str] = set()
        for d in decisions:
            entry = dict(
                product_id=d.product_id,
                name=t(PRODUCT_NAME, d.product_id, lang),
                name_en=str(self.products.loc[d.product_id].label_en),
                score=d.score, propensity=d.propensity, benefit=d.benefit,
                is_credit=bool(self.products.loc[d.product_id].is_credit),
                suppressed_by=d.suppressed_by)
            if d.shown:
                reasons = self.explainer.reasons(d.product_id, x, k=2, exclude=banned | used_keys)
                if reasons:
                    used_keys.add(reasons[0]["key"])
                entry["reasons"] = reasons
                entry["reason_line"] = self.reason_text(reasons[0]["key"], lang, phrase) if reasons else ""
                entry["benefit_line"] = t(PRODUCT_BENEFIT, d.product_id, lang)
                entry["reason_line_en"] = self.reason_text(reasons[0]["key"], "en", phrase) if reasons else ""
                entry["benefit_line_en"] = t(PRODUCT_BENEFIT, d.product_id, "en")
                entry["features_used"] = [r["feature"] for r in reasons]
                shown.append(entry)
            else:
                entry["reason_held"] = {
                    "STRESS_PAUSE": f"Credit offers are paused for {stress['pause_days']} days "
                                    f"because this customer is showing signs of financial stress.",
                    "NOT_ELIGIBLE": "Eligibility rule in policies/rules.yaml was not met.",
                    "BELOW_BENEFIT_FLOOR": "Benefit to the customer scored below the floor.",
                    "FREQUENCY_CAP": "This customer has already been nudged enough this week.",
                    "RANKED_BELOW": "Eligible and allowed, but it ranked below what we did show.",
                }.get(d.suppressed_by or "", d.suppressed_by or "")
                top = shown[0] if shown else None
                if d.suppressed_by in ("RANKED_BELOW", "FREQUENCY_CAP") and top \
                        and d.propensity > top["propensity"]:
                    entry["reason_held"] = (
                        f"Scored higher than {top['name_en']} on likelihood to accept "
                        f"({d.propensity:.2f} vs {top['propensity']:.2f}) but lower on customer "
                        f"benefit ({d.benefit:.2f} vs {top['benefit']:.2f}), so it ranked below.")
                    entry["outranked_by_benefit"] = True
                held.append(entry)

        result["recommendations"] = shown[:3]
        result["held_back"] = sorted(held, key=lambda h: -h["propensity"])
        result["bias_guard"] = {"dropped": BIAS_GUARDED,
                                "note": "Never passed to a model; kept only to measure fairness."}
        self._log_once(cid, as_of, shown, held, stress, fraud)
        return result

    def _public_features(self, f: pd.Series, lang: str = "en") -> list[dict]:
        labels = {
            "hi": {"monthly_income": "मासिक आय", "salary_regularity": "आय की नियमितता",
                   "emi_to_income": "EMI बनाम आय", "savings_rate": "बचत दर",
                   "cash_share": "नक़द ख़र्च का हिस्सा", "inflow_30d_delta": "पिछले महीने से आमदनी",
                   "avg_balance_30d": "औसत बैलेंस", "emi_bounce_90d": "छूटी EMI (90 दिन)",
                   "new_payee_7d": "नए पेयी (7 दिन)", "night_txn_share": "रात के ट्रांसफ़र"},
            "gu": {"monthly_income": "માસિક આવક", "salary_regularity": "આવકની નિયમિતતા",
                   "emi_to_income": "EMI સામે આવક", "savings_rate": "બચત દર",
                   "cash_share": "રોકડ ખર્ચનો ભાગ", "inflow_30d_delta": "ગયા મહિનાની સરખામણીએ આવક",
                   "avg_balance_30d": "સરેરાશ બેલેન્સ", "emi_bounce_90d": "ચૂકેલી EMI (90 દિવસ)",
                   "new_payee_7d": "નવા પેયી (7 દિવસ)", "night_txn_share": "રાત્રિના ટ્રાન્સફર"},
        }.get(lang, {})
        pretty = {
            "monthly_income": "Monthly income", "salary_regularity": "Income regularity",
            "emi_to_income": "EMI to income", "savings_rate": "Savings rate",
            "cash_share": "Cash share of spending", "inflow_30d_delta": "Inflow vs last month",
            "avg_balance_30d": "Average balance", "emi_bounce_90d": "EMIs missed (90d)",
            "new_payee_7d": "New payees (7d)", "night_txn_share": "Night-time transfers",
        }
        out = []
        for k, label in pretty.items():
            v = float(f[k])
            if k in ("monthly_income", "avg_balance_30d"):
                disp = inr(v)
            elif k in ("emi_bounce_90d", "new_payee_7d"):
                disp = str(int(v))
            elif k == "inflow_30d_delta":
                disp = f"{v * 100:+.0f}%"
            else:
                disp = f"{v:.2f}"
            out.append(dict(key=k, label=labels.get(k, label), value=round(v, 4), display=disp))
        return out

    def _log_once(self, cid, as_of, shown, held, stress, fraud) -> None:
        key = (cid, str(as_of))
        if key in self._logged:
            return
        self._logged.add(key)
        for e in shown:
            self.ledger.write(cid, "personalisation", "recommendation", as_of=as_of,
                              product_id=e["product_id"], shown=True, score=e["score"],
                              reason_codes=[r["key"] for r in e.get("reasons", [])],
                              features_used=e.get("features_used", []),
                              detail=e.get("reason_line_en", ""))
        for e in held:
            self.ledger.write(cid, "personalisation", "recommendation", as_of=as_of,
                              product_id=e["product_id"], shown=False, score=e["score"],
                              suppressed_by=e["suppressed_by"], detail=e.get("reason_held", ""))
        if stress.get("stressed"):
            self.ledger.write(cid, "stress_watch", "stress_flag", as_of=as_of,
                              score=stress["score"], reason_codes=[r["code"] for r in stress["fired"]],
                              detail=f"Credit paused {stress['pause_days']} days; hardship options shown.")
        if fraud.get("suspected"):
            self.ledger.write(cid, "fraud_watch", "fraud_flag", as_of=as_of,
                              score=fraud["score"], reason_codes=[r["code"] for r in fraud["fired"]],
                              detail="Protective hold placed; confirmation call queued.")

    def staff_queue(self, as_of: date, limit: int = 40) -> list[dict]:
        F = self.features_for(as_of)
        sc = self.stress.score_all(F)
        cust = self.fe.customers.set_index("customer_id")
        fr = pd.Series(self.fraud.anomaly(F), index=F.index)
        rows = []
        for cid, r in sc.sort_values("stress_score", ascending=False).head(limit).iterrows():
            c = cust.loc[cid]
            f = F.loc[cid]
            rows.append(dict(
                customer_id=cid, name=c["name"], city=c.city, language=c.language,
                occupation=c.occupation, stress_score=float(r.stress_score),
                stressed=bool(r.stressed), codes=[x for x in str(r.codes).split(",") if x],
                fraud_score=round(float(self.fraud.score(f.to_dict())["score"]), 3),
                monthly_income=inr(f.monthly_income),
                emi_to_income=round(float(f.emi_to_income), 2),
                inflow_30d_delta=round(float(f.inflow_30d_delta), 2)))
        return rows

    def fairness(self, as_of: date) -> dict:
        F = self.features_for(as_of)
        cust = self.fe.customers.set_index("customer_id").loc[F.index]
        sc = self.stress.score_all(F)
        probs = self.bank.predict_proba(F)
        benefit = self.products.benefit_score
        credit = self.products.is_credit
        good = probs[[p for p in probs.columns if not credit[p]]].mean(axis=1)
        panels = {}
        for attr in ["gender", "language", "city"]:
            g = pd.DataFrame({"attr": cust[attr].values,
                              "stress": sc.stressed.values.astype(float),
                              "good_offer": good.values}).groupby("attr")
            panels[attr] = [
                dict(group=str(k), n=int(len(v)),
                     stress_rate=round(float(v.stress.mean()), 3),
                     benefit_offer_rate=round(float(v.good_offer.mean()), 3))
                for k, v in g if len(v) >= 10]
        return dict(panels=panels, note="gender, language and city are excluded from every "
                                        "model input and used only for this panel.",
                    model_auc=self.auc)


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine
