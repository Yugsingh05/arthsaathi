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

## Running it in Docker

Nothing installed on the host — no uv, no Node. Each half owns its own Docker
setup: `backend/` and `frontend/` each have a Dockerfile, a `.dockerignore` and
a compose file, and each builds from its own directory as the build context.
Neither reaches outside itself, so either one runs, builds and deploys alone.

**Both halves together**

```bash
docker compose up --build
```

Then http://localhost:5173, API docs at http://localhost:8000/docs. The root
compose file builds nothing itself — it points at the two directories and wires
them together.

Boot is immediate, including the very first one. The dataset and the trained
model are committed to this repo, so the API image ships them rather than
regenerating them — `data/` is handed to the build as a named context, since it
sits beside `backend/` and is not part of that directory's build context. The
entrypoint still generates and trains, but only as a fallback when the
artefacts are genuinely absent. The web container waits on the API's
healthcheck, so the page is never served against a half-ready backend.

**Either half on its own**

```bash
cd backend  && docker compose up --build      # API alone on :8000
cd frontend && docker compose up --build      # web alone on :5173
```

The web container proxies `/api` to whatever `API_UPSTREAM` names. On its own
that defaults to port 8000 on the host, so it works against `uv run uvicorn` on
your machine or against `cd backend && docker compose up`; point it anywhere
else without rebuilding:

```bash
API_UPSTREAM=http://staging.internal:8000 docker compose up
```

Both stacks share the same two named volumes (`arthsaathi-data`,
`arthsaathi-models`), so switching between them never repeats work.

**Development, with hot reload on both halves:**

```bash
docker compose -f docker-compose.dev.yml up --build
```

Source is bind-mounted — edit a `.py` and uvicorn restarts, edit a `.jsx` and
Vite hot-reloads. It reuses the `data/` and `backend/models/` you already have
on the host rather than regenerating them.

**How it fits together**

```
backend/Dockerfile                 uv resolves deps into /opt/venv, runtime is
                                   python:3.12-slim
backend/docker-entrypoint.sh       generates data + trains models if missing
backend/docker-compose.yml         the API alone

frontend/Dockerfile                target dev     -> Vite dev server
                                   target runtime -> static build behind nginx
frontend/nginx/default.conf.*      serves dist, proxies /api, SPA fallback
frontend/docker-compose.yml        the web app alone

docker-compose.yml                 both, wired together; hands data/ to the
                                   API build as a named context
docker-compose.dev.yml             both, hot reload
```

Four things worth knowing if you change this.

`backend/Dockerfile` declares an empty `FROM scratch AS dataset` stage that the
compose files override with `additional_contexts: {dataset: ./data}`. That is
what lets the image carry the dataset while the build context stays `backend/`
alone — and a bare `docker build .` from `backend/` still succeeds, just with an
empty `/app/data` that the entrypoint then fills on first boot.

Inside the API image the tree is `/app/backend` and `/app/data`, because
`core/engine.py` resolves `DATA` as `backend/../data` — the two have to stay
siblings in the image even though only `backend/` is the build context.

The Python venv lives at `/opt/venv`, outside `/app`, so the dev bind mount over
`/app/backend` cannot shadow it.

nginx reaches the upstream through a variable rather than naming it directly in
`proxy_pass`. A literal name is resolved once at startup and nginx aborts if it
does not exist yet, which would stop the web container from booting whenever the
API is down — exactly what an independent frontend must survive. Through a
variable the name resolves per request, so the app still serves and only `/api`
returns 502. The resolver itself comes from the container's own `resolv.conf`
via `NGINX_ENTRYPOINT_LOCAL_RESOLVERS`; hardcoding Docker's `127.0.0.11` would
only be correct on a user-defined network.

The API image is ~2GB; xgboost, shap, scikit-learn and pyarrow account for most
of it. The web image is 76MB.

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
