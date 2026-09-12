from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FiredRule:
    id: str
    code: str
    says: str
    weight: float
    says_hi: str = ""
    says_gu: str = ""

    def text(self, lang: str) -> str:
        return (self.says_hi if lang == "hi" else self.says_gu if lang == "gu" else "") or self.says


@dataclass
class Decision:
    product_id: str
    shown: bool
    score: float
    propensity: float
    benefit: float
    reason_codes: list[str] = field(default_factory=list)
    suppressed_by: str | None = None


def safe_eval(expr: str, ctx: dict) -> bool:
    try:
        return bool(eval(expr, {"__builtins__": {}}, dict(ctx)))
    except Exception:
        return False


class PolicyEngine:
    def __init__(self, rules_path: str | Path):
        self.path = Path(rules_path)
        self.rules = yaml.safe_load(self.path.read_text())

    def eval_section(self, section: str, feats: dict) -> tuple[float, list[FiredRule]]:
        cfg = self.rules[section]
        fired: list[FiredRule] = []
        for r in cfg["rules"]:
            if safe_eval(r["when"], feats):
                fired.append(FiredRule(r["id"], r["code"], r["says"], float(r["weight"]),
                                       r.get("says_hi", ""), r.get("says_gu", "")))
        total = sum(f.weight for f in fired)
        return min(total, 1.0), fired

    def eligible(self, product_id: str, ctx: dict) -> bool:
        expr = self.rules["policy"]["eligibility"].get(product_id)
        return True if expr is None else safe_eval(expr, ctx)

    def apply(self, candidates: list[dict], ctx: dict, stressed: bool,
              nudges_this_week: int = 0) -> list[Decision]:
        p = self.rules["policy"]
        w = float(p["benefit_weight"])
        out: list[Decision] = []
        for c in candidates:
            score = w * c["benefit"] + (1 - w) * c["propensity"]
            d = Decision(product_id=c["product_id"], shown=True, score=round(score, 4),
                         propensity=round(c["propensity"], 4), benefit=round(c["benefit"], 4),
                         reason_codes=list(c.get("reason_codes", [])))
            if not self.eligible(c["product_id"], ctx):
                d.shown, d.suppressed_by = False, "NOT_ELIGIBLE"
            elif c["benefit"] < float(p["min_benefit_score"]):
                d.shown, d.suppressed_by = False, "BELOW_BENEFIT_FLOOR"
            elif stressed and c["is_credit"] and p["suppress_credit_when_stressed"]:
                d.shown, d.suppressed_by = False, "STRESS_PAUSE"
            out.append(d)

        out.sort(key=lambda d: (-d.shown, -d.score))
        limit = int(p["max_nudges_when_stressed"] if stressed else p["max_nudges_per_week"])
        cap = limit - int(nudges_this_week)
        shown = 0
        for d in out:
            if d.shown:
                if shown >= max(cap, 0):
                    d.shown = False
                    d.suppressed_by = "FREQUENCY_CAP" if nudges_this_week else "RANKED_BELOW"
                else:
                    shown += 1
        return out

    def in_quiet_hours(self, hour: int) -> bool:
        q = self.rules["policy"]["quiet_hours"]
        return not (int(q["start_hour"]) <= hour < int(q["end_hour"]))
