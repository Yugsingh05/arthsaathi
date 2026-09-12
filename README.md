# ArthSaathi

AI-powered hyper-personalized banking for Bharat. HackOut'26, DAIICT.

A layer that sits on top of a bank's existing core banking system. With the customer's
consent it reads their transactions, works out what's actually going on with their money,
and acts through a personalised home screen, an assistant that speaks their language, and
proactive help when it spots trouble. Bank staff get a console showing what the AI decided
and why.

The thing that makes it different: it will hold an offer back. If someone's income drops
and an EMI bounces, credit offers pause for 60 days and hardship options show up instead.
Every offer it decided not to show gets logged.

## Running it

```bash
./run.sh
```

Then http://localhost:5173. API docs at http://localhost:8000/docs.

First run generates the dataset and trains the models, which takes about 40 seconds.
After that everything is cached. No GPU, no API keys, no internet needed.

Two terminals if you prefer:

```bash
cd backend  && uv run uvicorn app.main:app --port 8000
cd frontend && npm run dev
```

See DEMO.md for the walkthrough.

## Code quality

SonarCloud analyses every push. The scanner always runs inside the
`sonarsource/sonar-scanner-cli` container — same image in CI and on your
machine — so local and CI reports never drift.

**One-time setup**

1. Sign in at [sonarcloud.io](https://sonarcloud.io) with GitHub and import
   `Yugsingh05/arthsaathi`. Keep the generated organization and project keys —
   if they differ from `yugsingh05` / `Yugsingh05_arthsaathi`, fix
   `sonar-project.properties`.
2. In the project's **Administration → Analysis Method**, turn
   **Automatic Analysis** *off*. It conflicts with CI-based analysis.
3. Generate a token at **My Account → Security**.
4. Add it to GitHub: **Settings → Secrets and variables → Actions → New
   repository secret**, named `SONAR_TOKEN`.
5. For local scans, put the same token in a git-ignored `.env`:
   `echo 'SONAR_TOKEN=your_token_here' >> .env`

**On push** — `.github/workflows/sonarcloud.yml` runs the scanner container and
uploads the report. Pull requests are analysed too and get inline comments.
The job summary links straight to the report.

**Locally, on Docker Desktop**

```bash
./scripts/sonar-scan.sh          # scans the current branch, prints the report URL
```

To scan automatically before every `git push`:

```bash
git config core.hooksPath scripts/hooks    # undo with: git config --unset core.hooksPath
```

The report lives at
<https://sonarcloud.io/project/overview?id=Yugsingh05_arthsaathi>.

Coverage is not reported yet — there is no test suite. When one lands, uncomment
the `sonar.tests` and coverage lines in `sonar-project.properties`.

## Layout

```
backend/
  app/core/features.py    narration parser + 21 point-in-time features
  app/core/segments.py    K-Means personas
  app/core/propensity.py  one XGBoost model per product
  app/core/explain.py     SHAP -> reason codes
  app/core/stress.py      YAML rules + IsolationForest
  app/core/fraud.py       velocity rules + IsolationForest
  app/core/policy.py      eligibility, gates, caps, ranking
  app/core/ledger.py      consent + reasoning ledger, DuckDB
  app/core/engine.py      decide() - ties it all together
  app/assistant/          loan and onboarding state machines
  policies/rules.yaml     thresholds, caps, eligibility
  scripts/                data generation and training
  app/core/exposures.py   large-borrower monitor, same rule engine
  app/data/cases.json     cited public-record detection-lag cases
frontend/src/views/       overview, customer 360, recommendations, risk,
                          journeys, portfolio, large exposures, audit
data/                     generated parquet + ledger db
```

## How it works

Transactions come in as narration strings. A regex parser pulls out the rail and
counterparty from things like `UPI/DR/41.../SWIGGY/YESB/swiggy@ybl/Payment`, then a
keyword classifier assigns a category. Agrees with ground truth 99.6% of the time.

Those become 21 features, all computed as of a given date so you can rewind the account
and see exactly what the system knew that morning. City, language, gender and device get
dropped before any model sees the data - they're kept only so the fairness panel can
measure outcomes by subgroup.

Four models score it: K-Means for segment, XGBoost per product for propensity, and
rules + IsolationForest for stress and fraud. SHAP explains each recommendation, using
only features that pushed the score up.

Everything then goes through `policy.py`, which is the only path from a score to a
screen. Eligibility, benefit floor, stress pause, frequency caps. Every candidate comes
back with a decision attached, shown or not, and all of it goes to the ledger.

## Some decisions worth explaining

**benefit_weight is 0.65.** Final rank is `0.65 * benefit + 0.35 * propensity`. That
number is the floor at which a recurring deposit scoring 0.92 on benefit still beats a
top-up loan scoring 0.95 on propensity. At 0.55 the loan wins - which is to say, below
that number the system sells. It's one line in rules.yaml.

**Stress is `rule_score + 0.25 * anomaly * (1 - rule_score)`, not a blend.** Blending
meant someone whose rules already justified action got rescued by looking statistically
normal. Rules set the floor, the IsolationForest only adds.

**Reasons only use positive SHAP contributions.** A feature pushing the score down isn't
a reason the customer is seeing something. There's also a contradiction guard in
`engine.py` so the system can't tell someone their income is dependable in the same week
it paused their credit for an income drop.

**Held-back offers are logged like shown ones.** Separately tracked as "not eligible",
"ranked below", "weekly cap" and "paused because they're struggling".

## Large exposures

The Large Exposures section has two halves and they are not the same kind of thing.

The case studies are real and cited - PNB's letters of undertaking, Kingfisher, Reliance
Home Finance - with a source link on every figure. They are there to show detection lag,
not to assert guilt, and each carries the denial on record. RBI put the average gap
between a fraud happening and a bank noticing at 22 months, and 55 months for frauds over
Rs 100 crore.

The 60 monitored borrowers are invented. Real names with invented financials would be
fabricating records about real people. They are scored by the same YAML rule engine as
retail, using a separate corporate rule set, so the transparency argument holds at both
scales.

## Caveats

The data is synthetic, deliberately - real customer data would breach the DPDP Act and
RBI localisation, which are the rules this thing is designed around. 500 customers, 8
personas, 12 months, with stress and fraud episodes injected.

The propensity labels are synthetic too. No bank gave us take-up history, so labels come
from a latent-utility model in `propensity.py` and XGBoost learns that mapping. Held-out
AUC is 0.61-0.82. Everything else - the pipeline, explanations, gates - is what it would
be on real labels.

The assistant is a state machine, not a chatbot. Set `LLM_API_KEY` and a hosted model
rephrases each step; leave it unset and it uses the scripted text. Journey completes the
same either way, which is why the demo doesn't need a network.

Not built: live Account Aggregator integration, uplift modelling, on-device Indic speech.

## Regulatory bits

| What | Where |
|---|---|
| DPDP purpose-specific, withdrawable consent | `core/ledger.py`, ledger tab |
| RBI FREE-AI: disclose, explain, human override | AI label, SHAP reasons, banker console |
| Fair Practices: contact hours, frequency caps | `rules.yaml` quiet_hours, max_nudges_per_week |
| Fairness | `BIAS_GUARDED` in `core/features.py`, fairness panel |
| Data localisation | everything runs in-region, no external calls |
