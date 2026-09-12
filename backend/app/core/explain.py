from __future__ import annotations

import numpy as np
import pandas as pd
import shap

from app.core.propensity import LATENT, PropensityBank

SPEAKABLE = {"savings_rate", "salary_regularity", "emi_to_income", "avg_balance_30d",
             "cash_share", "monthly_income", "income_volatility", "digital_share",
             "months_on_book", "discretionary_share"}


class Explainer:
    def __init__(self, bank: PropensityBank):
        self.bank = bank
        self._tree = {pid: shap.TreeExplainer(m) for pid, m in bank.models.items()}

    def reasons(self, product_id: str, x: pd.DataFrame, k: int = 2,
                exclude: set[str] | None = None) -> list[dict]:
        sv = self._tree[product_id].shap_values(x[self.bank.features])
        vals = np.asarray(sv).reshape(len(self.bank.features))
        s = pd.Series(vals, index=self.bank.features)
        s = s[[f for f in s.index if f in SPEAKABLE]]
        drivers = {f for f, w in LATENT.get(product_id, {}).items() if f != "_bias" and w > 0}
        pos = s[s > 0]
        s = pos if len(pos) else s
        rank = s.abs() * s.index.map(lambda f: 1.8 if f in drivers else 1.0)
        exclude = exclude or set()
        order = [f for f in rank.sort_values(ascending=False).index
                 if f"{f}{'+' if s[f] > 0 else '-'}" not in exclude]
        out = []
        for feat in order[:k]:
            out.append(dict(feature=feat, shap=round(float(s[feat]), 4),
                            direction="+" if s[feat] > 0 else "-",
                            key=f"{feat}{'+' if s[feat] > 0 else '-'}",
                            value=float(x.iloc[0][feat])))
        return out
