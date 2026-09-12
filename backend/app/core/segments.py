from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

SEGMENT_FEATURES = ["savings_rate", "emi_to_income", "cash_share", "income_volatility",
                    "avg_balance_30d", "months_on_book", "digital_share", "monthly_income",
                    "discretionary_share", "salary_regularity"]

NAMES = {
    ("savings_rate", "+"): "Steady saver",
    ("savings_rate", "-"): "Spending ahead of income",
    ("emi_to_income", "+"): "Stretched borrower",
    ("emi_to_income", "-"): "Debt-light earner",
    ("cash_share", "+"): "Cash-first earner",
    ("cash_share", "-"): "Fully digital",
    ("income_volatility", "+"): "Variable income",
    ("income_volatility", "-"): "Predictable income",
    ("avg_balance_30d", "+"): "Balance builder",
    ("avg_balance_30d", "-"): "Thin balance",
    ("months_on_book", "+"): "Long-standing customer",
    ("months_on_book", "-"): "New to the bank",
    ("digital_share", "+"): "Fully digital",
    ("digital_share", "-"): "Cash-first earner",
    ("monthly_income", "+"): "Higher income",
    ("monthly_income", "-"): "Low, irregular income",
    ("discretionary_share", "+"): "Lifestyle spender",
    ("discretionary_share", "-"): "Essentials only",
    ("salary_regularity", "+"): "Salaried regular",
    ("salary_regularity", "-"): "Irregular earner",
}


class SegmentModel:
    def __init__(self, k: int = 6):
        self.k = k
        self.scaler = StandardScaler()
        self.km = KMeans(n_clusters=k, n_init=10, random_state=42)
        self.labels_: dict[int, str] = {}
        self.profile_: pd.DataFrame | None = None

    def fit(self, X: pd.DataFrame) -> "SegmentModel":
        Z = self.scaler.fit_transform(X[SEGMENT_FEATURES])
        self.km.fit(Z)
        centres = pd.DataFrame(self.km.cluster_centers_, columns=SEGMENT_FEATURES)
        used: set[str] = set()
        for i, row in centres.iterrows():
            for feat in row.abs().sort_values(ascending=False).index:
                name = NAMES[(feat, "+" if row[feat] > 0 else "-")]
                if name not in used:
                    used.add(name)
                    self.labels_[int(i)] = name
                    break
            else:
                self.labels_[int(i)] = f"Segment {i}"
        self.profile_ = X[SEGMENT_FEATURES].groupby(self.predict(X)).mean().round(3)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.km.predict(self.scaler.transform(X[SEGMENT_FEATURES]))

    def name(self, cluster: int) -> str:
        return self.labels_.get(int(cluster), f"Segment {cluster}")
