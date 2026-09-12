from __future__ import annotations


import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core.policy import PolicyEngine

STRESS_FEATURES = ["inflow_30d_delta", "savings_rate", "emi_to_income", "emi_bounce_90d",
                   "min_balance_30d", "balance_volatility", "cash_share", "income_volatility"]


class StressModel:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(n_estimators=200, contamination=0.12, random_state=42)

    def fit(self, X: pd.DataFrame) -> "StressModel":
        Z = self.scaler.fit_transform(X[STRESS_FEATURES])
        self.iforest.fit(Z)
        return self

    def anomaly(self, X: pd.DataFrame) -> np.ndarray:
        Z = self.scaler.transform(X[STRESS_FEATURES])
        raw = -self.iforest.score_samples(Z)
        return np.clip((raw - 0.40) / 0.25, 0, 1)

    def score(self, feats: dict, lang: str = "en") -> dict:
        rule_score, fired = self.policy.eval_section("stress", feats)
        cfg = self.policy.rules["stress"]
        anom = float(self.anomaly(pd.DataFrame([feats]))[0])
        score = float(np.clip(rule_score + cfg["anomaly_weight"] * anom * (1 - rule_score), 0, 1))
        return dict(
            score=round(score, 3),
            rule_score=round(rule_score, 3),
            anomaly=round(anom, 3),
            stressed=score >= float(cfg["threshold"]),
            threshold=float(cfg["threshold"]),
            pause_days=int(cfg["credit_pause_days"]),
            fired=[dict(id=f.id, code=f.code, says=f.text(lang), weight=f.weight) for f in fired],
        )

    def score_all(self, X: pd.DataFrame) -> pd.DataFrame:
        anom = self.anomaly(X)
        cfg = self.policy.rules["stress"]
        rows = []
        for i, (cid, row) in enumerate(X.iterrows()):
            rs, fired = self.policy.eval_section("stress", row.to_dict())
            s = rs + cfg["anomaly_weight"] * anom[i] * (1 - rs)
            rows.append(dict(customer_id=cid, stress_score=round(float(s), 3),
                             rule_score=round(rs, 3), anomaly=round(float(anom[i]), 3),
                             stressed=s >= cfg["threshold"],
                             codes=",".join(f.code for f in fired)))
        return pd.DataFrame(rows).set_index("customer_id")
