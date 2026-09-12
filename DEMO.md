# Demo walkthrough

Start with `./run.sh`, then open the links in order. Each one restores the exact state so
you're not clicking around under pressure.

Runs entirely on the laptop. If the wifi dies nothing changes.

## Opening

India built the best payment rails in the world but not banking that works for the last
500 million people on them. Kiran delivers food in Rajkot. Here's three moments in his year.

## 1. A normal month

http://localhost:5173/?c=CUST0001&t=2026-07-04&lang=gu&tab=overview

The suggestion is in Gujarati and it leads with the reason, not the product: you've saved
₹3,000 a month for six months, a recurring deposit pays 6.5%.

Tap "આ મને કેમ દેખાય છે?" to show the SHAP values and which fields were used.

Right-hand panel is what the system knew on that date and nothing after it.

## 2. Money gets tight

http://localhost:5173/?c=CUST0001&t=2026-08-22&lang=gu&tab=overview

This is the one to spend time on.

Income down 40%, one EMI bounced. Stress score 0.65 with two rules fired by name. The
loan banner every other app would show is gone - instead there's an EMI holiday, a
restructure, and a call back.

Scroll the held-back list: Personal Loan, paused because they're struggling.

Line to use: every bank in India has the data to spot that month. None of them hold the
offer back.

Then try taking a loan anyway:

http://localhost:5173/?c=CUST0001&t=2026-09-12&lang=gu&tab=journeys

Pick a purpose, 50000, 24 months. It refuses at the affordability check and offers
hardship instead. The state machine also won't let it skip a KYC step.

## 3. Something looks wrong

http://localhost:5173/?c=CUST0001&t=2026-09-12&lang=gu&tab=overview

Four transfers, ₹38,000, 2am, payees never paid before. Protective hold plus a
confirmation call in Gujarati. Not a silent freeze.

## 4. The ledger

http://localhost:5173/?c=CUST0001&t=2026-09-12&lang=gu&tab=audit

Every offer shown, every offer held back, every flag, with purpose and reasons. Read the
counter out: 42 shown, 244 held back.

Toggle personalisation off, go back to the app, suggestions stop immediately and banking
is untouched.

Then the console:

http://localhost:5173/?c=CUST0001&t=2026-09-12&lang=en&tab=portfolio

Officer sees the same reasons, can override, and the fairness panel shows outcome rates
by gender, language and city - none of which are model inputs.

## Closing

It's the first banking personalisation engine built to say "not now, here's help
instead" - and to show the customer every time it did.

## If something breaks

| Problem | Fix |
|---|---|
| "Cannot reach the backend" | `cd backend && uv run uvicorn app.main:app --port 8000` |
| DuckDB lock error | Two API processes. `pkill -f "uvicorn app.main"` then start one |
| Ledger counts inflated from rehearsing | `rm data/arthsaathi.duckdb`, restart the API |
| Numbers drifted after editing | `uv run python scripts/generate_data.py && uv run python scripts/train.py` |
| Mic does nothing | Web Speech API is Chrome only. Typing works everywhere |
| Port 5173 taken | `npm run dev -- --port 5174` |

## Other customers

Meena, Bhavnagar, Hindi - http://localhost:5173/?c=CUST0002&t=2026-09-12&lang=hi&tab=overview

Her top-up loan scores higher on propensity than the recurring deposit and still loses on
benefit. The held-back card shows both numbers.

Rafiq, kirana store - http://localhost:5173/?c=CUST0003&t=2026-09-12&lang=gu&tab=overview

UPI soundbox merchant, hundreds of small daily credits parsed off the narration.
