from __future__ import annotations


import numpy as np
import pandas as pd
from xgboost import XGBClassifier

LATENT: dict[str, dict[str, float]] = {
    "rd_2000":          {"_bias": -0.5, "savings_rate": 1.5, "salary_regularity": 0.8,
                         "emi_to_income": -0.6, "discretionary_share": -0.3},
    "sip_1000":         {"_bias": -0.8, "savings_rate": 1.1, "digital_share": 0.7,
                         "monthly_income": 0.5, "months_on_book": 0.3, "age": -0.4},
    "sweep_fd":         {"_bias": -1.0, "avg_balance_30d": 1.6, "balance_volatility": -0.5},
    "health_cover":     {"_bias": -0.9, "age": 0.9, "monthly_income": 0.6, "emi_to_income": -0.3},
    "accident_cover":   {"_bias": -0.6, "cash_share": 0.4, "income_volatility": 0.5,
                         "monthly_income": -0.3},
    "kcc":              {"_bias": -1.5, "income_volatility": 1.0, "cash_share": 0.8,
                         "monthly_income": 0.3},
    "gold_loan":        {"_bias": -1.2, "cash_share": 0.9, "emi_to_income": 0.4, "savings_rate": -0.6},
    "two_wheeler_loan": {"_bias": -1.3, "monthly_income": 0.6, "age": -0.5,
                         "emi_to_income": -0.3, "digital_share": 0.3},
    "personal_loan":    {"_bias": -0.9, "emi_to_income": 0.8, "discretionary_share": 0.7,
                         "savings_rate": -0.9, "monthly_income": 0.4},
    "top_up_loan":      {"_bias": -1.0, "emi_to_income": 1.0, "credit_utilisation_proxy": 0.6,
                         "savings_rate": -0.7},
    "credit_card":      {"_bias": -1.1, "digital_share": 0.9, "discretionary_share": 0.8,
                         "monthly_income": 0.6, "salary_regularity": 0.4},
}


def synth_labels(X: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    Z = (X - X.mean()) / X.std().replace(0, 1)
    out = {}
    for pid, coefs in LATENT.items():
        logit = np.full(len(X), coefs["_bias"], dtype=float)
        for f, w in coefs.items():
            if f != "_bias":
                logit += w * Z[f].to_numpy()
        p = 1 / (1 + np.exp(-logit))
        out[pid] = (rng.random(len(X)) < p).astype(int)
    return pd.DataFrame(out, index=X.index)


class PropensityBank:

    def __init__(self) -> None:
        self.models: dict[str, XGBClassifier] = {}
        self.features: list[str] = []

    def fit(self, X: pd.DataFrame, y: pd.DataFrame) -> "PropensityBank":
        self.features = list(X.columns)
        for pid in y.columns:
            m = XGBClassifier(n_estimators=180, max_depth=4, learning_rate=0.08,
                              subsample=0.9, colsample_bytree=0.9, reg_lambda=1.2,
                              eval_metric="logloss", random_state=42)
            m.fit(X, y[pid])
            self.models[pid] = m
        return self

    def predict_proba(self, X: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            {pid: m.predict_proba(X[self.features])[:, 1] for pid, m in self.models.items()},
            index=X.index)
