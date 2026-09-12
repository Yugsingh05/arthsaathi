from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from app.assistant.engine import Assistant
from app.core.engine import get_engine
from app.core.exposures import ExposureBook
from app.i18n.templates import LANG_NAMES
from app.schemas import (AssistantReply, AssistantStart, ConsentUpdate, InterventionRequest,
                         OverrideRequest)

router = APIRouter(prefix="/api")


def _as_of(s: str | None) -> date:
    e = get_engine()
    return date.fromisoformat(s) if s else date.fromisoformat(e.meta["today"])


@router.get("/meta")
def meta(lang: str = "en") -> dict:
    from app.core.engine import CHECKPOINT_TR, OCCUPATION_TR
    e = get_engine()
    checkpoints = []
    for c in e.meta["checkpoints"]:
        tr = CHECKPOINT_TR.get(lang, {}).get(c["label"])
        checkpoints.append({**c, "label": tr[0] if tr else c["label"],
                            "sub": tr[1] if tr else c["sub"]})
    demo = [e.customer(c) for c in e.meta["demo_customers"]]
    return dict(
        checkpoints=checkpoints, today=e.meta["today"],
        languages=[{"code": k, "name": v} for k, v in LANG_NAMES.items()],
        demo_customers=[{**{k: v for k, v in c.items() if k != "account_opened"},
                         "occupation": OCCUPATION_TR.get(lang, {}).get(c["occupation"], c["occupation"])}
                        for c in demo],
        products=e.fe.products.to_dict("records"),
        model_auc=e.auc, ledger=e.ledger.counts(),
        policy=e.policy.rules["policy"],
        stress_rules=e.policy.rules["stress"]["rules"],
        fraud_rules=e.policy.rules["fraud"]["rules"])


@router.get("/customers")
def customers(q: str = "", limit: int = 60) -> list[dict]:
    e = get_engine()
    df = e.fe.customers
    needle = q.strip()
    if needle:
        cols_q = ["name", "customer_id", "city", "occupation", "persona_label"]
        mask = False
        for col in cols_q:
            mask = mask | df[col].astype(str).str.contains(needle, case=False, regex=False, na=False)
        df = df[mask]
    cols = ["customer_id", "name", "persona_label", "city", "language", "occupation", "age"]
    return df[cols].head(limit).to_dict("records")


@router.get("/customer/{cid}")
def customer(cid: str, as_of: str | None = None, lang: str | None = None) -> dict:
    e = get_engine()
    if cid not in set(e.fe.customers.customer_id):
        raise HTTPException(404, "unknown customer")
    return e.decide(cid, _as_of(as_of), lang)


@router.get("/customer/{cid}/transactions")
def transactions(cid: str, as_of: str | None = None, limit: int = 40) -> list[dict]:
    e = get_engine()
    import pandas as pd
    t = e.fe.txns
    t = t[(t.customer_id == cid) & (t.txn_date <= pd.Timestamp(_as_of(as_of)))]
    t = t.sort_values(["txn_date", "hour"], ascending=False).head(limit)
    out = t[["txn_id", "txn_date", "hour", "amount", "direction", "parsed_rail",
             "parsed_category", "counterparty", "narration", "balance_after"]].copy()
    out["txn_date"] = out.txn_date.dt.strftime("%d %b %Y")
    return out.where(out.notna(), None).to_dict("records")


@router.get("/customer/{cid}/timeline")
def timeline(cid: str, as_of: str | None = None) -> dict:
    e = get_engine()
    import pandas as pd
    hi = pd.Timestamp(_as_of(as_of))
    t = e.fe.txns
    t = t[(t.customer_id == cid) & (t.txn_date <= hi) & (t.txn_date > hi - pd.Timedelta(days=365))].copy()
    t["ym"] = t.txn_date.dt.to_period("M").astype(str)
    g = t.groupby(["ym", "direction"]).amount.sum().unstack(fill_value=0.0)
    inflow = g.get("credit", pd.Series(dtype=float))
    outflow = g.get("debit", pd.Series(dtype=float))
    months = sorted(set(inflow.index) | set(outflow.index))
    partial = hi.strftime("%Y-%m") if hi.day < 28 else None
    rows = [dict(month=m,
                 inflow=round(float(inflow.get(m, 0.0)), 2),
                 outflow=round(float(outflow.get(m, 0.0)), 2),
                 net=round(float(inflow.get(m, 0.0) - outflow.get(m, 0.0)), 2))
            for m in months if m != partial]
    return dict(months=rows,
                categories=[dict(category=k.replace("_", " "), amount=round(float(v), 2))
                            for k, v in t[t.direction.eq("debit")]
                            .groupby("parsed_category").amount.sum()
                            .sort_values(ascending=False).head(7).items()])


@router.get("/customer/{cid}/ledger")
def ledger(cid: str, limit: int = 60) -> dict:
    e = get_engine()
    return dict(entries=e.ledger.entries(cid, limit), consents=e.ledger.consents(cid),
                counts=e.ledger.counts())


@router.post("/customer/{cid}/consent")
def consent(cid: str, body: ConsentUpdate) -> dict:
    e = get_engine()
    return dict(consents=e.ledger.set_consent(cid, body.purpose, body.granted))


@router.post("/intervention")
def intervention(body: InterventionRequest) -> dict:
    e = get_engine()
    as_of = _as_of(body.as_of)
    messages = {
        "emi_holiday": "One EMI deferred by 30 days. No late fee, no credit bureau report.",
        "restructure": "Tenure extended by 6 months; monthly amount reduced.",
        "call_back": "Branch call-back queued in the customer's language for today.",
        "confirm_fraud": "Customer confirmed the transfers were not theirs. Hold stays; case raised.",
        "release_hold": "Customer confirmed the transfers. Protective hold released.",
        "request_product": "Customer asked to know more. Queued for a branch call, no commitment taken.",
        "talk_to_banker": "Customer asked to speak to a person about this suggestion.",
    }
    if body.action not in messages:
        raise HTTPException(400, "unknown action")
    if "fraud" in body.action or "hold" in body.action:
        purpose = "fraud_watch"
    elif body.action in ("request_product", "talk_to_banker"):
        purpose = "personalisation"
    else:
        purpose = "stress_watch"
    eid = e.ledger.write(body.customer_id, purpose, f"intervention:{body.action}",
                         as_of=as_of, detail=messages[body.action])
    return dict(ok=True, entry_id=eid, message=messages[body.action])


@router.post("/assistant/start")
def assistant_start(body: AssistantStart) -> dict:
    e = get_engine()
    return Assistant(e).start(body.customer_id, body.flow, body.lang, _as_of(body.as_of))


@router.post("/assistant/reply")
def assistant_reply(body: AssistantReply) -> dict:
    e = get_engine()
    return Assistant(e).reply(body.session_id, body.text)


@router.get("/exposures")
def exposures() -> dict:
    e = get_engine()
    book = ExposureBook(e.policy)
    return dict(summary=book.summary(), rows=book.all(),
                rules=e.policy.rules["corporate"]["rules"],
                threshold=e.policy.rules["corporate"]["threshold"])


@router.get("/exposures/cases")
def exposure_cases() -> dict:
    return ExposureBook(get_engine().policy).cases


@router.get("/exposures/{exposure_id}")
def exposure_detail(exposure_id: str) -> dict:
    row = ExposureBook(get_engine().policy).detail(exposure_id)
    if row is None:
        raise HTTPException(404, "unknown exposure")
    return row


@router.get("/staff/queue")
def staff_queue(as_of: str | None = None, limit: int = 40) -> list[dict]:
    return get_engine().staff_queue(_as_of(as_of), limit)


@router.get("/staff/fairness")
def staff_fairness(as_of: str | None = None) -> dict:
    return get_engine().fairness(_as_of(as_of))


@router.post("/staff/override")
def staff_override(body: OverrideRequest) -> dict:
    e = get_engine()
    eid = e.ledger.write(body.customer_id, "stress_watch", f"officer_{body.decision}",
                         detail=f"{body.officer}: {body.note or body.decision}")
    return dict(ok=True, entry_id=eid)
