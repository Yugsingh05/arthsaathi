from __future__ import annotations

import re
import uuid
from datetime import date

from app.assistant.flows import FLOWS, NO, YES, Step
from app.i18n.templates import inr

SESSIONS: dict[str, dict] = {}

RATES = {"vehicle": 10.5, "business": 13.0, "medical": 12.0, "education": 9.5}


def kfs(amount: float, months: int, rate: float) -> dict:
    r = rate / 1200
    emi = amount * r * (1 + r) ** months / ((1 + r) ** months - 1)
    total = emi * months
    fee = round(amount * 0.01, 0)
    return dict(
        amount=round(amount), months=months, rate=rate, emi=round(emi),
        total_repayable=round(total + fee), total_interest=round(total - amount),
        processing_fee=fee, apr=round(rate + 1.1, 2),
        prepayment="No charge for prepayment after 6 months.",
        lines=[f"You borrow {inr(amount)}.",
               f"You repay {inr(emi)} every month for {months} months.",
               f"You pay {inr(total - amount)} as interest and {inr(fee)} as a one-time fee.",
               f"In total you repay {inr(total + fee)}.",
               "No charge for prepayment after 6 months."])


class Assistant:
    def __init__(self, engine):
        self.engine = engine

    def start(self, customer_id: str, flow: str, lang: str, as_of: date) -> dict:
        sid = uuid.uuid4().hex[:10]
        SESSIONS[sid] = dict(session_id=sid, customer_id=customer_id, flow=flow, lang=lang,
                             as_of=str(as_of), idx=0, slots={}, transcript=[])
        return self._emit(SESSIONS[sid], first=True)

    def reply(self, session_id: str, text: str) -> dict:
        s = SESSIONS.get(session_id)
        if not s:
            return {"error": "session not found"}
        steps: list[Step] = FLOWS[s["flow"]]
        if s["idx"] >= len(steps):
            # the journey is over; anything further is a no-op rather than an
            # IndexError, because the caller may still have an open input box
            return self._finish(s)
        step = steps[s["idx"]]
        s["transcript"].append({"who": "customer", "text": text})

        # The step waiting on this reply can be a computed one — after the Key
        # Facts Statement, the reply is the customer accepting it. There is no
        # slot to fill, so hand straight to _emit and let it run the step; the
        # old code incremented past it, which is how the closing message was
        # being skipped.
        if step.kind == "computed":
            return self._emit(s)

        if step.kind == "consent":
            if NO.match(text.strip()):
                s["slots"][step.slot] = False
                s["idx"] += 1
                return self._emit(s, note="Refused. The journey continues with another document.")
            if not YES.match(text.strip()):
                return self._emit(s, error=True)
            s["slots"][step.slot] = True
        elif step.kind == "choice":
            ids = [c["id"] for c in (step.choices or [])]
            pick = next((i for i in ids if i.lower() in text.lower()), None)
            if pick is None:
                return self._emit(s, error=True)
            s["slots"][step.slot] = pick
        elif step.validate:
            m = re.match(step.validate, text.strip())
            if not m:
                return self._emit(s, error=True)
            s["slots"][step.slot] = (m.group(1).replace(",", "") if m.groups() else text.strip())

        s["idx"] += 1
        return self._emit(s)

    def _emit(self, s: dict, first: bool = False, error: bool = False,
              note: str | None = None) -> dict:
        steps: list[Step] = FLOWS[s["flow"]]
        lang = s["lang"]

        # A computed step either returns a payload of its own or just falls
        # through. The last step of every flow is the closing message, which
        # falls through — so remember its text rather than losing it.
        closing = ""
        while s["idx"] < len(steps) and steps[s["idx"]].kind == "computed" and not error:
            step = steps[s["idx"]]
            out = self._computed(s, step)
            if out is not None:
                return out
            closing = step.ask.get(lang) or step.ask["en"]
            s["idx"] += 1

        if s["idx"] >= len(steps):
            return self._finish(s, closing)

        step = steps[s["idx"]]
        msg = (step.error.get(lang) or step.error.get("en") or step.ask.get(lang)) if error \
            else (step.ask.get(lang) or step.ask["en"])
        s["transcript"].append({"who": "assistant", "text": msg})
        return dict(session_id=s["session_id"], step=step.id, kind=step.kind, message=msg,
                    choices=[{"id": c["id"], "label": c.get(lang, c["en"])} for c in (step.choices or [])],
                    mandatory=step.mandatory_note.get(lang) or step.mandatory_note.get("en"),
                    note=note, slots=s["slots"], done=False, error=error,
                    script_locked=True, transcript=s["transcript"])

    def _finish(self, s: dict, closing: str = "") -> dict:
        """The terminal payload, carrying the flow's closing message."""
        if closing and not (s["transcript"] and s["transcript"][-1].get("text") == closing):
            s["transcript"].append({"who": "assistant", "text": closing})
        return dict(session_id=s["session_id"], step="done", kind="done",
                    message=closing, choices=[], mandatory=None, note=None,
                    done=True, error=False, slots=s["slots"],
                    transcript=s["transcript"])

    def _computed(self, s: dict, step: Step) -> dict | None:
        lang, cid = s["lang"], s["customer_id"]
        as_of = date.fromisoformat(s["as_of"])

        if step.id == "affordability":
            view = self.engine.decide(cid, as_of, lang)
            f = {x["key"]: x["value"] for x in view["features"]}
            amount = float(s["slots"].get("amount", 0))
            months = int(s["slots"].get("tenure", 24))
            rate = RATES.get(s["slots"].get("purpose", "business"), 13.0)
            k = kfs(amount, months, rate)
            new_ratio = (f["emi_to_income"] * f["monthly_income"] + k["emi"]) / max(f["monthly_income"], 1)
            s["slots"]["kfs"] = k
            s["slots"]["new_emi_ratio"] = round(new_ratio, 2)

            if view["stress"]["stressed"]:
                msg = {
                    "en": "I am going to stop here. Your income has fallen and an EMI did not go through recently, so a new loan would make this month harder, not easier. You can take a one-month EMI holiday instead, or a bank officer can call you today.",
                    "hi": "मैं यहीं रुकूँगा। आपकी आमदनी घटी है और हाल में एक EMI नहीं कट पाई, इसलिए नया लोन इस महीने को आसान नहीं, मुश्किल बनाएगा। आप एक महीने की EMI छुट्टी ले सकते हैं, या बैंक अधिकारी आज आपको कॉल करेगा।",
                    "gu": "હું અહીં જ અટકીશ. તમારી આવક ઘટી છે અને તાજેતરમાં એક EMI કપાઈ નથી, તેથી નવી લોન આ મહિનાને સરળ નહીં, મુશ્કેલ બનાવશે. તમે એક મહિનાની EMI રજા લઈ શકો છો, અથવા બેંક અધિકારી આજે તમને ફોન કરશે.",
                }[lang if lang in ("en", "hi", "gu") else "en"]
                s["transcript"].append({"who": "assistant", "text": msg})
                self.engine.ledger.write(cid, "stress_watch", "loan_journey_stopped", as_of=as_of,
                                         score=view["stress"]["score"],
                                         reason_codes=[r["code"] for r in view["stress"]["fired"]],
                                         detail="Loan journey halted at affordability check; hardship offered.")
                return dict(session_id=s["session_id"], step="stress_stop", kind="stress_stop",
                            message=msg, done=True, halted=True, slots=s["slots"],
                            stress=view["stress"], transcript=s["transcript"],
                            offer=["emi_holiday", "restructure", "call_back"])

            if new_ratio > 0.5:
                msg = {
                    "en": f"At {inr(k['emi'])} a month, your EMIs would take {new_ratio:.0%} of your income. I can offer a longer tenure so the monthly amount is smaller.",
                    "hi": f"{inr(k['emi'])} महीने पर आपकी EMI आपकी आय का {new_ratio:.0%} हो जाएगी। मैं लंबी अवधि दे सकता हूँ ताकि मासिक रक़म कम हो।",
                    "gu": f"{inr(k['emi'])} પ્રતિ માસે તમારી EMI તમારી આવકના {new_ratio:.0%} થઈ જશે. હું લાંબી મુદત આપી શકું જેથી માસિક રકમ ઓછી થાય.",
                }[lang if lang in ("en", "hi", "gu") else "en"]
                s["transcript"].append({"who": "assistant", "text": msg})
                s["slots"]["affordability_warning"] = msg
            return None

        if step.id == "kfs":
            k = s["slots"].get("kfs")
            msg = step.ask.get(lang, step.ask["en"])
            s["transcript"].append({"who": "assistant", "text": msg})
            s["idx"] += 1
            self.engine.ledger.write(cid, "personalisation", "loan_kfs_shown", as_of=as_of,
                                     detail=f"KFS shown: {k['amount']} at {k['rate']}% for {k['months']}m")
            return dict(session_id=s["session_id"], step="kfs", kind="kfs", message=msg,
                        kfs=k, done=False, slots=s["slots"], transcript=s["transcript"])
        return None
