# Plan: expand Part 1 of the ADK logging tutorial with cloud deployments

Tutorial: `ai/adk/logging/TUTORIAL.md`. Goal: take Part 1's "dumbest possible
logging" (plain `logging.basicConfig` + a level, no JSON, no plugins) to the
cloud and observe what actually lands in Cloud Logging, *before* the tutorial
teaches structured logging in Part 6. This gives Part 1 a cloud payoff and sets
up Part 6's "fact one" (stderr → ERROR) with evidence instead of assertion.

## The three asks, restated

| # | Ask | Proposed shape |
|---|---|---|
| 1 | Deploy `01_log_levels.py` to Cloud Run; do console logs reach Cloud Logging? | **Cloud Run Job** (see decision D1) running the script once per execution |
| 2 | Stripped-down FastAPI API server for the same logic, on Cloud Run | New `examples/09_min_api.py` + deploy script → Cloud Run **service** |
| 3 | Same demonstration on Agent Runtime, native ADK logging only | Two variants (see D4): native agent deploy (1.6) and the same API container via the `/api` passthrough (1.7) |

## Decisions / assumptions (review these)

- **D1: Script as a job, not a service.** `01_log_levels.py` runs once and
  exits; it listens on no port, so a Cloud Run *service* would fail its
  readiness check. A **Cloud Run Job** is the closest equivalent: run it with
  `--args=info|debug|warning`; each execution's console output flows to Cloud
  Logging. Alternative: wrap it in a throwaway HTTP shim to force it into a
  service. Rejected because it breaks the "unmodified script" point.
  *If you specifically want a service for #1, say so and I'll do the shim.*

- **D2: result of #1 — prediction was WRONG, corrected from live run.**
  Predicted: `basicConfig` on stderr → **ERROR** severity in Cloud Logging.
  Actual (2026-09-03, `adk-logging-job`): the `basicConfig` lines *are* on
  stderr (confirmed via `logName ...%2Fstderr`), but Cloud Logging recorded
  them with **blank/Default severity, not ERROR**. The `print()`ed answer is on
  stdout, also Default. So the "stderr = ERROR on Cloud Run" rule that Part 6
  cites does **not** reproduce on a Cloud Run *Job*. The section must teach the
  real finding, not the folklore. The clean, reproducible lesson that DID hold:
  the level dial works in the cloud — the `--args=warning` execution shows the
  `===== WARNING =====` + answer with **zero** `google_adk`/tool lines, while
  the `info` execution shows the full five-line lifecycle. (Whether stderr→ERROR
  holds on a Cloud Run *service*, 1.5, is a separate live check — do not assume
  it matches the Job.)

- **D3: API server stays deliberately naive.** No UI. Same shape as example
  02 minus its uvicorn `log_config`: uvicorn runs with its defaults, so the
  bare `INFO:` access lines from Part 1.3 appear as-is. One `POST /chat`
  endpoint runs the Part 1.1 question through the agent; a `GET /healthz` for
  Cloud Run. Logging config = exactly Part 1.1's `configure(level)`, level
  from a `LOG_LEVEL` env var at startup: plain text, no JSON formatter, no
  trace field. This shows all three text streams (yours, `google_adk`,
  uvicorn access) interleaved raw in Cloud Logging.

- **D4: Agent Runtime scope, two variants.** Equivalent of #1 (native
  agent deploy, 1.6): set the log level via env var `LOG_LEVEL` read in the
  agent module, deploy with `adk deploy agent_engine`, send one query, read
  `aiplatform.googleapis.com/reasoning_engine_stdout`. Equivalent of #2 (1.7,
  bring-your-own-container): deploy OUR own FastAPI server as a custom
  container, not the agent object. The container is constrained: Agent
  Runtime's runtime contract requires it to listen on **8080** and implement
  `POST /api/reasoning_engine` and `POST /api/stream_reasoning_engine` with a
  `{"class_method","input"}` body, so a plain `/chat` route is not enough. The
  smallest server that satisfies this wraps the agent in
  `vertexai.agent_engines.AdkApp` and dispatches the named method (pattern from
  the Google "deploy a containerized agent" codelab). Deploy = build/push the
  image to Artifact Registry, then register it with the `vertexai` SDK
  (`agent_engines.create(container_spec=..., class_methods=..., env_vars=...)`);
  no `gcloud` CLI exists for Agent Runtime. Query through the `/api` passthrough
  (`.../reasoningEngines/v1/{resource}/api/api/stream_reasoning_engine` — the
  passthrough prefix plus the container's own `/api` route), authenticated with
  Google credentials. **Built and locally verified** (both endpoints serve; the
  naive Part 1 logs appear).

- **D7-CONFIRMED (live, 1.6): the platform overrides our logging.** On native
  Agent Runtime the tool line arrives as
  `2026-09-03 21:51:45,037 - INFO - agent.py:53 - tool get_weather called...`
  — the ADK CLI's timestamped `file:line` format, NOT our `basicConfig`
  format (`INFO - demo_agent.agent - message`), which never appears. The
  runtime installs its own handler, so `basicConfig(format=...)` is a no-op
  there (exactly the D7 risk). Two more live facts: (1) agent/framework lines
  land on `aiplatform.googleapis.com/reasoning_engine_stderr`, while
  `_stdout` carries only the uvicorn access lines — so read by
  `resource.type=".../ReasoningEngine"`, not by the stdout log name (both the
  runbook and deploy script were fixed). (2) severity is blank/Default on
  stderr, same as 1.4/1.5.

- **D7: `LOG_LEVEL` mechanics, verified vs predicted.** Verified: env vars at
  deploy time are documented for both targets (`--update-env-vars`). Not
  verifiable from docs: whether the hosting runtime installs root handlers
  before the agent module imports, which would make a bare
  `logging.basicConfig(level=...)` a silent no-op. Mitigation: call
  `basicConfig` *and* explicitly `setLevel` the root and `google_adk` loggers;
  the setLevel calls apply regardless of existing handlers. The 1.6 verify
  step (deploy at INFO, redeploy at WARNING, diff the logs) is the live proof
  the dial works.

- **D5: Where it lands in TUTORIAL.md.** New subsections **1.4, 1.5, 1.6**
  (one per ask) at the end of Part 1, each in the existing
  Why / Do this / You will see / What it means voice, with real captured
  output. Parts 6/8 get one-line back-references ("you saw the raw version in
  1.4/1.6"). Verification-status section updated.

- **D6: Tooling.** Plain `gcloud` (`gcloud run jobs deploy`,
  `gcloud run deploy --source`) matching the existing `deploy/` scripts' style,
  not `agents-cli`, since this tutorial folder isn't a scaffolded project.
  Project/region via `PROJECT_ID` / `REGION` env vars, same as today.

## New / changed files

| File | Purpose |
|---|---|
| `examples/09_min_api.py` | Minimal FastAPI app: `POST /chat` runs the Part 1.1 logic, `GET /healthz`. Uvicorn defaults, level from `LOG_LEVEL`, no JSON logging on purpose. |
| `deploy/deploy_job.sh` | Build + deploy `01_log_levels.py` as Cloud Run Job; helper to execute at a chosen level. |
| `deploy/deploy_api.sh` | Deploy the API server as a Cloud Run service (default: require auth, test with an identity token). |
| `deploy/Dockerfile.job`, `deploy/Dockerfile.api` | Minimal images (reuse existing `deploy/Dockerfile` as base if it fits). |
| `TUTORIAL.md` | New 1.4 / 1.5 / 1.6 + cross-links + verification status. |
| `deploy/deploy_agent_engine.sh` | Small change if needed: pass `LOG_LEVEL` env var through. |
| `demo_agent/agent.py` | Tiny addition: honor `LOG_LEVEL` env var at import (needed for 1.6; harmless elsewhere). |

## Execution checklist

1. [x] **1.4 Cloud Run Job**: `Dockerfile.job` + `deploy_job.sh` written.
       Deploy/execute + log capture pending a live run.
2. [x] **1.5 API server**: `09_min_api.py` written and **verified locally** —
       all three streams (agent.server, google_adk, uvicorn access) appear as
       plain text, matching 1.1/1.3. `Dockerfile.api` + `deploy_api.sh`
       (`--allow-unauthenticated`) written. Cloud deploy + capture pending.
3. [x] **1.6 Agent Runtime (native)**: `LOG_LEVEL` handling added to
       `demo_agent/agent.py` (guarded on env var so examples 01-08 unaffected;
       basicConfig + explicit setLevel per D7). `deploy_agent_engine.sh`
       updated to write `LOG_LEVEL` into `demo_agent/.env` (no env-var flag on
       `adk deploy agent_engine`; it carries the agent dir's .env). Deploy +
       capture pending.
4. [x] **1.7 Agent Runtime (custom container)**: built in
       `agent_runtime_byoc/` (`main.py`, `Dockerfile`, `requirements.txt`,
       copied `demo_agent/`, `deploy_byoc.py`, `deploy_byoc.sh`). **Locally
       verified** — both contract endpoints serve, agent reaches the model,
       naive Part 1 logs present. `vertexai` SDK shapes checked against the
       installed 2.1.0 (`container_spec`, `class_methods`, `env_vars`,
       `agent_framework` all valid; `AdkApp` import path confirmed). Cloud
       build + register + passthrough query + log capture pending a live run.
5. [x] **TUTORIAL.md**: 1.4-1.7 written from live output; Part 6 "Fact one"
       corrected (stderr→Default, not ERROR); Part 6/8 back-references added;
       Part 8 stream/read-command fixed; "How to choose" table + best-practice
       summary + verification-status all updated.
6. [x] **Cleanup guidance**: teardown commands in each deploy script; runbook
       has a consolidated teardown block. (Resources still live on jwd-gcp-demos
       pending teardown run.)

## Live-run findings (all four sections verified against jwd-gcp-demos)

- **1.4 (Job):** basicConfig lines on stderr = **Default severity, not ERROR**
  (D2 prediction wrong). Level dial works (warning run empty, info full).
- **1.5 (service):** all four streams land as plain text; same Default-not-ERROR
  on stderr; WARNING silences framework/tool but uvicorn access lines persist
  (Part 2 preview). The `WARNING`-severity rows are Cloud Run's `requests` log
  (404s), not our app.
- **1.6 (native AR):** level is ours (`LOG_LEVEL`), but format/stream/severity
  are the platform's (ADK CLI `agent.py:53` format on `reasoning_engine_stderr`,
  Default severity). Redeploy makes a NEW engine.
- **1.7 (BYOC):** our basicConfig format SURVIVES (contrast with 1.6). Two real
  traps found + fixed: (a) needs **project-level** `artifactregistry.reader` on
  the aiplatform + aiplatform-re agents (repo-level was insufficient); (b)
  reserved `GOOGLE_CLOUD_*` vars force model region to deploy region → 404,
  worked around with `MODEL_LOCATION` copied in main.py before agent import.

## Open questions for Jeff

- D1: Job OK for ask #1, or do you want a service shim?
- 1.5 auth: plan assumes require-auth (identity-token curl). Say so if you
  prefer `--allow-unauthenticated`.
