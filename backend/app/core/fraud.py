from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.core.policy import PolicyEngine

FRAUD_FEATURES = ["night_txn_share", "new_payee_7d", "large_debit_share",
                  "balance_volatility", "distinct_payees_90d", "min_balance_30d"]


class FraudModel:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy
        self.scaler = StandardScaler()
        self.iforest = IsolationForest(n_estimators=200, contamination=0.06, random_state=42)

    def fit(self, X: pd.DataFrame) -> "FraudModel":
        self.iforest.fit(self.scaler.fit_transform(X[FRAUD_FEATURES]))
        return self

    def anomaly(self, X: pd.DataFrame) -> np.ndarray:
        raw = -self.iforest.score_samples(self.scaler.transform(X[FRAUD_FEATURES]))
        return np.clip((raw - 0.40) / 0.25, 0, 1)

    def score(self, feats: dict, recent_txns: pd.DataFrame | None = None, lang: str = "en") -> dict:
        rule_score, fired = self.policy.eval_section("fraud", feats)
        cfg = self.policy.rules["fraud"]
        anom = float(self.anomaly(pd.DataFrame([feats]))[0])
        score = float(np.clip(rule_score + cfg["anomaly_weight"] * anom * (1 - rule_score), 0, 1))
        flagged: list[dict] = []
        if recent_txns is not None and len(recent_txns):
            sus = recent_txns[(recent_txns.hour < 5) & recent_txns.direction.eq("debit")]
            flagged = sus.assign(txn_date=sus.txn_date.dt.strftime("%Y-%m-%d")).to_dict("records")
        return dict(
            score=round(score, 3), rule_score=round(rule_score, 3), anomaly=round(anom, 3),
            suspected=score >= float(cfg["threshold"]), threshold=float(cfg["threshold"]),
            action=cfg["hold_action"] if score >= float(cfg["threshold"]) else "monitor",
            fired=[dict(id=f.id, code=f.code, says=f.text(lang), weight=f.weight) for f in fired],
            flagged_transactions=flagged[:8],
        )
