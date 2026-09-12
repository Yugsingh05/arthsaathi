from __future__ import annotations

from app.core.policy import PolicyEngine
from app.db.documents import load_document, load_exposures

GRADES = [(0.75, "critical"), (0.55, "high"), (0.15, "watch"), (0.0, "standard")]


def grade(score: float) -> str:
    for cut, name in GRADES:
        if score >= cut:
            return name
    return "standard"


class ExposureBook:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy
        self.rows = load_exposures()
        self.cases = load_document("cases", default={})

    def score_one(self, row: dict) -> dict:
        score, fired = self.policy.eval_section("corporate", row)
        threshold = float(self.policy.rules["corporate"]["threshold"])
        return dict(
            **{k: v for k, v in row.items() if k not in ("collateral_series", "debt_series")},
            risk_score=round(score, 3),
            grade=grade(score),
            flagged=score >= threshold,
            fired=[dict(code=f.code, says=f.says, weight=f.weight) for f in fired],
        )

    def all(self) -> list[dict]:
        return sorted((self.score_one(r) for r in self.rows),
                      key=lambda r: -r["risk_score"])

    def detail(self, exposure_id: str) -> dict | None:
        for r in self.rows:
            if r["exposure_id"] == exposure_id:
                out = self.score_one(r)
                out["collateral_series"] = r["collateral_series"]
                out["debt_series"] = r["debt_series"]
                return out
        return None

    def summary(self) -> dict:
        scored = self.all()
        flagged = [r for r in scored if r["flagged"]]
        return dict(
            entities=len(scored),
            total_exposure_cr=round(sum(r["exposure_cr"] for r in scored), 1),
            flagged=len(flagged),
            flagged_exposure_cr=round(sum(r["exposure_cr"] for r in flagged), 1),
            by_grade={g: sum(1 for r in scored if r["grade"] == g)
                      for _, g in GRADES},
        )
