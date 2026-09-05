# Rewrite the ADK OpenTelemetry tutorial (Part 5 + Part 6 telemetry)

Folder: `ai/adk/logging/`. Status: **ALL STAGES 1–8 DONE** (2026-09-05).
Part 5 (5.0–5.8) and Part 6 telemetry (6.1–6.4) rewritten, other-backends
reference (5.7), logging interplay (5.8), and cross-refs/link-check complete.
Two NEEDS-RUN items remain (not blockers): 5.5's Cloud Run deploy of
`08_otel_server.py`, and the open question of where native Agent Runtime OTel
telemetry lands (verified negative: `gen_ai.*`/traces did not surface; see Part 7).
Research done 2026-09-04
against the tutorial's own venv (`ai/adk/logging/.venv`: google-adk 2.8.0,
google-cloud-aiplatform 2.1.0, opentelemetry-sdk 1.42.1, Python 3.13.3).

Citation shorthand: `adk/<path>:<line>` means
`ai/adk/logging/.venv/lib/python3.13/site-packages/google/adk/<path>`;
`vertexai/adk.py` means `.../site-packages/vertexai/agent_engines/templates/adk.py`;
`otel-sdk/…` and `gcp-logging/…` are the installed OpenTelemetry packages in the
same site-packages. Line numbers are from the 2.8.0 install.

> Trap for whoever executes this: `ai/adk/.venv` (a sibling) holds google-adk
> **2.5.0** on Python 3.14 and is first on PATH in some shells. Every command in
> this plan runs as `ai/adk/logging/.venv/bin/...`.

---

## Status update (Jeff, runs verified)

5.1–5.4 have been executed and verified by Jeff outside the 2026-09-04 Fable
session below; 5.5/5.6 and the example-08 restructure were then written against
the verified deploy script and source citations. **Stages 1–4 are done**
(5.0–5.6). Stage 3 is split into 3a (5.3) and 3b (5.4), both done. The disclaimers
in the 2026-09-04 session log below still describe only what *that* session ran;
they no longer bound the project's status. Remaining: Stage 5 (Part 6 telemetry),
Stage 6 (5.7), Stage 7 (5.8), Stage 8 (cross-refs).

5.4/5.5/5.6 build notes:
- 5.4 is **inline copy-paste commands** (`adk deploy cloud_run --otel_to_cloud`,
  curl the service, read `gen_ai.*` in Logs Explorer, teardown), matching the
  5.1-5.3 step style. Jeff's call: no wrapper script for 5.4 — the reader runs
  the deploy command directly. `deploy/deploy_otel_cloudrun.sh` was **deleted**.
- 5.4 reads the turn back from **Logs Explorer** (`gen_ai.*`), not Cloud Trace —
  this is a logging tutorial. The Cloud Trace curl step and the Dockerfile-`CMD`
  demonstration were cut; the two deploy traps a reader can actually hit
  (`adk deploy` exits 0 on failure; the `[otel-gcp]` boot-crash) are one short
  aside, everything else dropped.
- **5.5 REDESIGNED (2026-09-05), see `docs/adk-otel-5.5-redesign.md`.** Jeff's
  correction: 5.5 is now a **minimal OTel server** (`08_otel_server.py`, renamed
  from `08_otel_cloud.py`), not an InMemoryRunner script. Logging-only. Verified
  live locally (server + `/chat` + `gen_ai.*` in Cloud Logging + `.env` content
  knob before/after). Cloud Run deploy is inline commands + `deploy/Dockerfile.otel_server`,
  NEEDS-RUN. The 5.6 console-exporter aside was cut (span exporter, off-topic for
  logging).
- 5.5/5.6 carry forward references to **5.7** (env-var table), which Stage 6 has
  not written yet.

## Session log (2026-09-04, session model Fable 5.1)

This records only what I ran and observed in this session. It does **not** cover
the 5.0-5.4 prose, `deploy/deploy_otel_cloudrun.sh`, or the untracked
`ai/adk/logging/jwd/` directory now present in the working tree: those were
written outside this session and I did not execute the 5.3/5.4 runs their
verification status describes. Treat that content as unverified by me.

**Environment confirmed.** `ai/adk/logging/.venv/bin/adk --version` → 2.8.0,
Python 3.13.3. Port 8000 free. Docker 28.4.0. ADC project `jwd-gcp-demos`,
identity `jeff@jwdavis.me` (owner). Telemetry, Cloud Trace, Logging, Monitoring
APIs all enabled.

**Stage 1 — done and verified.** All four corrections applied (see checked
steps below). `grep -n "automatically" tutorial/06-agent-runtime.md
deploy/deploy_agent_engine.sh` returns nothing (exit 1); "before ADK is
imported" is gone from `tutorial/` and `examples/`. `bash -n` passes on the two
edited scripts; `08_otel_cloud.py` still parses.

**Stage 2 — partially run.** What I executed:

- **5.1 (plain `adk web`, one London turn):** the seven expected spans read back
  from `/dev/apps/demo_agent/debug/trace/session/{id}` with nothing configured
  (trace `3037b29d…`). Tree matches the plan's expected names. Answer: "The
  weather in London is currently 15°C and drizzling."
- **`otel/check_local.sh` written and passing (exit 0).** Correction to the plan:
  it uses **`adk web`, not `adk api_server`**. `adk api_server` installs the same
  in-memory exporters but registers **no `/dev` debug routes** (confirmed 404 on
  both `/dev/.../debug/trace/{event_id}` and `.../session/{id}`; `/openapi.json`
  lists no debug paths). Only `DevServer` (`cli/dev_server.py:463`,
  `:796-822`), used by `adk web`, mounts them. **This contradicts plan Q3's claim**
  that api_server's in-memory spans are reachable through the `/dev/.../debug/trace`
  endpoints. See Open question note below.
- **5.2 "before" (`adk web --otel_to_cloud`, no `[otel-gcp]`, no knob):** exported
  to Cloud Trace (trace `2d442bd3…`, all 7 spans, project-scoped via
  `gcp.project_id`). `gen_ai.*` log events landed in Cloud Logging with content
  `<elided>` and matching `trace`/`spanId`. Startup WARNING text matches the plan
  verbatim: `Unable to import GoogleGenAiSdkInstrumentor - some telemetry will be
  disabled. Make sure to install google-adk[otel-gcp]` (`api_server.py:747`). The
  `call_llm` spans carried the **full** `gcp.vertex.agent.llm_request` /
  `_response` (knob demo "before" state confirmed).
- **Metrics 400 diagnosed (new finding, replaces the plan's `workload.googleapis.com`
  ASSUMPTION):** the server logged repeated `Failed to export metrics batch code:
  400`. Reproduced against `telemetry.googleapis.com/v1/metrics` with ADK's own
  `_get_gcp_otlp_metric_exporter` + `get_gcp_resource`. The endpoint maps the
  metric to the **`prometheus_target`** monitored resource, which requires a
  `service.instance.id` and a real `cloud.region`. `get_gcp_resource(project)` on
  a laptop sets neither, so every batch is rejected:
  - no extra attrs → `INVALID_ARGUMENT: prometheus_target resource type must have
    an instance specified`
  - `service.instance.id` only → `INVALID_ARGUMENT: write for resource failed:
    Unrecognized region or location`
  - `service.instance.id` + `cloud.region=us-central1` → **200**
  - `cloud.region=global` → `INVALID_ARGUMENT: location / region / zone label
    cannot be set to "global"`
  - The env route works too: `OTEL_RESOURCE_ATTRIBUTES=service.name=…,
    service.instance.id=…,cloud.region=us-central1` (picked up by
    `OTELResourceDetector` inside `get_gcp_resource`) → 200.
  So locally, metrics export needs those resource attributes; spans and logs do
  not. (I did not confirm the metric *type* name in Cloud Monitoring; the 200
  writes above used a synthetic point, not a real agent run.)
- **`google-adk[otel-gcp]` doubling question (open question 5):** dry-run
  install lists what the extra adds (`opentelemetry-instrumentation-google-genai
  0.7b1`, `-grpc`, `-httpx`, `opentelemetry-util-genai`, `wrapt`). I did **not**
  install it or run a turn with it, so the doubling question is **not resolved by
  me.** Marked NEEDS-RUN.

**Cloud hygiene.** I deployed nothing to Cloud Run or Agent Engine. The only
cloud writes were the two `adk web --otel_to_cloud` local runs (traces/logs to
`jwd-gcp-demos`) and a handful of synthetic metric points during the 400
diagnosis.

---

## Coverage table

| #   | Problem                                                       | Resolved by                                                                           | How we know it is resolved                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| --- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | No `adk web` + OTel switch/env-var coverage                   | Stage 2                                                                               | 5.1 shows the Trace tab in the `adk web` UI with nothing configured; 5.2 runs `adk web --otel_to_cloud` locally and reads the `gen_ai.*` events back in Logs Explorer, with one Trace Explorer check for the span knob (as shipped — not logs-only). States plainly that no `.env` variable can turn the Cloud export on, and that the `OTEL_*` vars must be shell exports (Q1 finding).                                                                                                             |
| P2  | Same gap for `adk api_server`                                 | Stage 3                                                                               | 5.3 repeats 5.2 with `adk api_server --otel_to_cloud` + curl, same read-backs; states the two commands share one code path (`fast_api_common_options`, `_setup_telemetry`). 5.4 ships the same flag to Cloud Run with `adk deploy cloud_run --otel_to_cloud`.                                                                                                                                                                                                                                       |
| P3  | Readers write OTel config code that may be unnecessary        | Stages 2–4                                                                            | 5.1 through 5.4 configure telemetry with **zero** agent code (a flag, or nothing). 5.5 is the one place code is needed, and says why: you wrote your own server, so you make the two calls the CLI would have made. Example `08_otel_server.py` is a minimal server whose only added lines are those two calls. Human check: no OTel code appears before 5.5.                                                                                                                                        |
| P4  | Agent Runtime telemetry not addressed                         | Stage 5                                                                               | 6.1 names the one switch and its two routes. 6.2 deploys with the flag, 6.3 deploys with the `.env` var only; both are read back in Cloud Trace, Cloud Logging, and the deployment's env list. The current "traces appear automatically" claim is replaced by "the platform decides when you set neither; do not rely on it."                                                                                                                                                                       |
| P5  | Console span output as the primary path                       | Stage 2 (cut), Stage 4 (cut entirely)                                                 | The rewritten Part 5 has no console-exporter step anywhere. The 5.6 "debugging aid" aside was **removed** (Jeff, 2026-09-05): a `ConsoleSpanExporter` is a *span* exporter, off-topic for a logging tutorial. Grep check: `ConsoleSpanExporter` does not appear in `tutorial/`.                                                                                                                                                                                                                     |
| P6  | No guidance on other OTel collectors                          | Stages 4, 6                                                                           | 5.5 shows the OTLP code variant for a custom server (snippet, not run); 5.7 documents the env-var route for CLI-launched servers (endpoint, headers, http/protobuf only, shell env not `.env`) and points to the adk.dev integrations list. Nothing is run against a non-Google backend (Jeff's call, 2026-09-04), so P6 is covered by documentation and a human read, not by execution.                                                                                                            |
| P7  | No sample output / explanation                                | Every content stage (2–7)                                                             | Each scenario has an **Expected output** block captured from a real run and a **What you are looking at** callout naming each span/attribute/log field. Human check per stage.                                                                                                                                                                                                                                                                                                                      |
| P8  | Interplay with logging plugins and ADK-native logging ignored | Stage 1 (corrections), Stage 2 (knob demo), Stage 5 (knobs on Agent Runtime), Stage 7 | 5.2 shows the span-attribute knob before/after once, and the best-practice value stays in `.env` for every later run. 6.2/6.3 show which enablement route sets the knob for you and which does not, via the deployment env lists. 5.8 runs one turn with DEBUG logs + `LoggingPlugin` + OTel export simultaneously and shows the same turn in four places, then states independent/correlated/duplicated per pair and the two content knobs. Stage 1 fixes the wrong "no knob" warning immediately. |

---

## Research findings

### Q1. Can an ADK agent emit OTel telemetry from env vars alone?

**Yes for CLI-launched agents (`adk web`, `adk api_server`, `adk deploy cloud_run`)
and for Agent Runtime. No for a plain Python script or a hand-written server:
those need exactly one zero-argument call.** So P3 holds with a qualification,
not a contradiction.

Evidence:

- `maybe_set_otel_providers()` appends generic OTLP exporters whenever
  `OTEL_EXPORTER_OTLP_ENDPOINT` or a signal-specific `OTEL_EXPORTER_OTLP_{TRACES,METRICS,LOGS}_ENDPOINT`
  is set: `adk/telemetry/setup.py:45-56` (docstring), `:124-147` (`_get_otel_exporters`).
  Resource attributes come from `OTEL_SERVICE_NAME` / `OTEL_RESOURCE_ATTRIBUTES`
  via `OTELResourceDetector`: `setup.py:118-121`.
- The only caller inside ADK is the CLI server: `adk/cli/api_server.py:649-666`
  (`_setup_telemetry`), `:668-677` (`_otel_env_vars_enabled`), `:721-735`
  (`_setup_telemetry_from_env`), wired from `ApiServer.get_fast_api_app` at
  `api_server.py:1173`. `runners.py` never sets a provider (its only OTel use is
  `context.get_current()` at `:598`, `:1389`); `cli/cli.py` (`adk run`) has no
  telemetry setup at all (grep: no hits).
- Empirical check (this session, no model call): with
  `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:4318/v1/traces`, importing
  `InMemoryRunner` leaves a `ProxyTracerProvider` (nothing exports); calling the
  CLI's `_setup_telemetry(otel_to_cloud=False)` yields a `TracerProvider` with
  `BatchSpanProcessor(OTLPSpanExporter → http://localhost:4318/v1/traces)`.
  Logger/meter providers stay proxies when only the traces var is set, as the
  code predicts.
- Docs agree: adk.dev/observability/traces/ ("export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=… then `adk web`"),
  adk.dev/observability/metrics/ (same pattern with `_METRICS_ENDPOINT`),
  adk.dev/observability/logging/ (`OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`).

Limits of the env-var path:

| Limit                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Evidence                                                                                                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Needs `opentelemetry-exporter-otlp-proto-http`; not a base dependency of google-adk (only `opentelemetry-api`/`-sdk` are).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `google_adk-2.8.0.dist-info/METADATA:32-33`; otlp-proto-http appears only under extras `gcp`/`all`/`test` (`:97`, `:193`, `:249`). Already in the tutorial's `requirements.txt`.                                          |
| HTTP/protobuf only. ADK imports the `proto.http` exporters; no gRPC exporter is imported or installed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `setup.py:150-167`. `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`: **not found** in ADK code.                                                                                                                                        |
| Headers/timeout come from the OTel SDK's own env handling (`OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_EXPORTER_OTLP_TIMEOUT`), not from ADK.                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/                                                                                                                                                          |
| GenAI SDK auto-instrumentation only if `google-adk[otel-gcp]` is installed; otherwise a WARNING is logged at startup. Not installed in the tutorial venv today.                                                                                                                                                                                                                                                                                                                                                                                                                                                  | `api_server.py:738-748`; observed warning text: `Unable to import GoogleGenAiSdkInstrumentor - some telemetry will be disabled.`                                                                                          |
| Content knobs are separate env vars: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (default `NO_CONTENT`), `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` (default **true**), `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`, `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN` (1 or 2), `ADK_EXPERIMENTAL_TELEMETRY`.                                                                                                                                                                                                                                                                                           | `adk/telemetry/context.py:38-47`, `:85-118`; `adk/telemetry/_schema_version.py:40-91`                                                                                                                                     |
| No CLI ⇒ one call: `maybe_set_otel_providers()` with no args honors the same env vars.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | `setup.py:45-72` (hooks default to empty, env exporters still appended at `:74`).                                                                                                                                         |
| **`.env` cannot carry the `OTEL_*` vars for `adk web` / `adk api_server`.** The agent's `.env` is loaded lazily when the agent is first loaded, after the server is built; `_setup_telemetry` runs at server construction. Only the deprecated `--trace_to_cloud` branch loads `.env` at startup. So the vars must be in the shell environment (`env.sh`), not `demo_agent/.env`.                                                                                                                                                                                                                                | `adk/cli/utils/agent_loader.py:331-332` (lazy load), `api_server.py:1173` (setup at construction), `adk/cli/fast_api.py:314-318` (the deprecated branch), `adk/cli/utils/envs.py:53-81`. Resolves former open question 9. |
| **No env var selects the Google Cloud branch.** `_setup_telemetry` enters the GCP path only on the `--otel_to_cloud` flag. `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` set locally only adds a `User-Agent` header to an exporter that must already exist. The only env-var-only route to Google is the generic OTLP path with a hand-supplied bearer token (`OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://telemetry.googleapis.com/v1/traces`, `OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer …`, `OTEL_RESOURCE_ATTRIBUTES=gcp.project_id=…`): one-hour token, traces only. **Not run**; not a tutorial path. | `api_server.py:649-666`; `adk/telemetry/_agent_engine.py:203-205`; `google_cloud.py:_get_gcp_span_exporter` (uses an `AuthorizedSession`, which the plain OTLP exporter cannot).                                          |

### Q2. What does `adk web` do with the OTel switch and env vars?

Flag: `--otel_to_cloud` ("Whether to write OTel data to Google Cloud
Observability services - Cloud Trace and Cloud Logging"); `--trace_to_cloud` is
deprecated in favor of it (both from `adk web --help`, captured this session;
deprecation callback `_deprecate_trace_to_cloud` in `adk/cli/cli_tools_click.py`).

Decision order in `_setup_telemetry` (`api_server.py:649-666`):

1. `--otel_to_cloud` → `_setup_gcp_telemetry` (`:680-718`): `google.auth.default()`
   for credentials and project, `get_gcp_exporters(enable_cloud_tracing=True,
   enable_cloud_metrics=True, enable_cloud_logging=True)`, resource from
   `get_gcp_resource(project_id)`. Traces and metrics go to
   `telemetry.googleapis.com/v1/{traces,metrics}` over OTLP
   (`adk/telemetry/google_cloud.py:57-69`), logs via `CloudLoggingExporter`
   (`google_cloud.py:264-281`, import is unguarded, so
   `opentelemetry-exporter-gcp-logging` is required). Then the GenAI SDK
   instrumentor if installed.
2. else any `OTEL_EXPORTER_OTLP_*_ENDPOINT` set → `_setup_telemetry_from_env`.
3. else a bare `TracerProvider` carrying only the dev UI's in-memory exporters.

In every branch the dev UI exporters are installed (`ApiServerSpanExporter`,
`InMemoryExporter`: `api_server.py:458`, `:483`, `:1170-1178`) and served at
`/dev/apps/{app}/debug/trace/{event_id}` and `.../debug/trace/session/{id}`
(`adk/cli/dev_server.py:796-804`). So `adk web` has an in-process Trace tab with
no flags at all; the switch and env vars only add **export**.

What is auto-instrumented (all from ADK itself, no extra packages):

| Signal     | Names                                                                                                                                                                                                                                       | Source                                                                                                                                                                                                                                              |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Spans      | `invocation` (root, schema v1), `invoke_agent {name}`, `call_llm`, `generate_content {model}`, `execute_tool {tool}`; also `send_data`, `execute_tool (merged)`, `compact_events …`, `handle_context_caching`                               | `adk/telemetry/_instrumentation.py:133,476,509`; `adk/flows/llm_flows/base_llm_flow.py:1732`, `:717`; `adk/flows/llm_flows/functions.py:526,774`; `adk/telemetry/tracing.py:1067,1121`; `adk/apps/compaction.py:60`; `adk/models/google_llm.py:245` |
| Log events | `gen_ai.system.message`, `gen_ai.user.message`, `gen_ai.choice` (stable semconv path); `gen_ai.client.inference.operation.details` under the experimental opt-in                                                                            | `tracing.py` emit sites (`otel_logger.emit`), `adk/telemetry/_stable_semconv.py:46-130`, `_experimental_semconv.py:619-636`                                                                                                                         |
| Metrics    | `gen_ai.invoke_agent.duration`, `gen_ai.invoke_workflow.duration`, `gen_ai.execute_tool.duration`, `gen_ai.invoke_agent.inference_calls`, `gen_ai.invoke_agent.tool_calls`, `gen_ai.client.operation.duration`, `gen_ai.client.token.usage` | `adk/telemetry/_metrics.py:47-137`; adk.dev/observability/metrics/                                                                                                                                                                                  |

Not instrumented: inbound HTTP (no FastAPI/ASGI instrumentation; the only
middleware extracts `Google-Agent-Engine-Traceparent`, `adk/cli/fast_api.py:531-547`,
`adk/telemetry/_agent_engine.py:26-52`); Python `logging` (no `LoggingHandler`
anywhere in ADK, grep: no hits); httpx/gRPC clients (only when
`GOOGLE_CLOUD_AGENT_ENGINE_ID` is set and the extras are installed,
`api_server.py:749-767`); Cloud Run's `X-Cloud-Trace-Context`/`traceparent`
(**not found**: no extraction code).

### Q3. Same for `adk api_server`

Identical. Both commands take the same option group (`fast_api_common_options`,
`cli_tools_click.py`) and both construct the server through
`ApiServer.get_fast_api_app`, which is where `_setup_telemetry` runs
(`api_server.py:1173`). `adk web` only adds `web_assets_dir` (the UI,
`fast_api.py`). The one practical difference: with `api_server` there is no Trace
tab, so without export the in-memory spans are reachable only through the
`/dev/.../debug/trace` endpoints above.

> **CORRECTION (2026-09-04 run, Fable 5.1).** The `/dev/.../debug/trace`
> endpoints are **not** available under `adk api_server`. `_setup_telemetry`
> still installs the same in-memory exporters, but only `DevServer` (used by
> `adk web`, `cli/dev_server.py:463`, `:796-822`) registers the `/dev` routes;
> the `web=False` path uses plain `ApiServer` and mounts none of them
> (`cli/fast_api.py:265-285`). Confirmed by a live probe: both
> `/dev/apps/demo_agent/debug/trace/{event_id}` and `.../session/{id}` return
> **404** on `adk api_server`, and `/openapi.json` lists no debug paths. So with
> `api_server` and no export, the in-memory spans are **not reachable at all**.
> `otel/check_local.sh` therefore uses `adk web`, not `api_server`. This changes
> the P2 "how we know" note and the 5.3 wording (5.3 must read spans back from
> Cloud Trace after `--otel_to_cloud`, or from `adk web`, not from an
> `api_server` debug endpoint).

Cloud Run via the CLI: `adk deploy cloud_run --otel_to_cloud` writes the flag into
the container `CMD adk {web|api_server} … --otel_to_cloud` (`adk/cli/cli_deploy.py:216`),
so the same path runs in the cloud under the service account's ADC, and
`get_gcp_resource` merges `GoogleCloudResourceDetector` attributes
(`google_cloud.py`, requires `opentelemetry-resourcedetector-gcp`, installed).
The tutorial dropped `adk deploy cloud_run` in the Part 4–6 merge (see
`docs/adk-logging-merge-parts-4-6.md`, decision 3); this plan does not bring it back.

### Q4. How does telemetry work in Agent Runtime?

**One switch.** On Agent Runtime, telemetry is controlled by a single
environment variable on the Reasoning Engine's `deployment_spec.env`:
`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`. The `AdkApp` wrapper reads it at
startup (`vertexai/adk.py:1767-1793`): `true`/`1` ⇒ on, `false`/`0` ⇒ off,
anything else (including the literal `unspecified`) ⇒ None. With the legacy
`enable_tracing` constructor argument left at its default, the truth table at
`vertexai/adk.py:1795-1815` reduces to: **tracing on only when the env var is
true**. Logging is "always enabled when telemetry is enabled" (`:1767-1778`).
Unlike `adk web --otel_to_cloud`, no flag reaches the process on Agent Runtime;
every tool below is just a different way to write that env var.

| Way to set it                                                                                                                | What it writes                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Evidence                                                                                                                                                                                                                                                                                           |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `adk deploy agent_engine --otel_to_cloud` (the tutorial's `deploy_agent_engine.sh`)                                          | `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` **and** `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (unless `.env` already sets it) into `env_vars`, then `vertexai.Client().agent_engines.create(config=…)`.                                                                                                                                                                                                                                                  | `cli_deploy.py:1273-1282`, `:1293-1300`, `:1305-1430`                                                                                                                                                                                                                                              |
| `adk deploy agent_engine` without the flag, with `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` in the agent dir's `.env` | Same env var, and the CLI prints that the flag was set by `.env`. No `ADK_CAPTURE…` default.                                                                                                                                                                                                                                                                                                                                                                      | `cli_deploy.py:1283-1291`                                                                                                                                                                                                                                                                          |
| `agents-cli deploy` (target `agent_runtime`, v1.1.0 installed here)                                                          | `setdefault` of the same var to `true`, plus `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`; project `.env` is the base layer and `--update-env-vars` wins. The scaffolded Terraform sets the same two vars. The scaffolded app also calls `setup_agent_engine_telemetry()`, which invokes `vertexai`'s private `_default_instrumentor_builder` itself and passes `otel_to_cloud=False` to ADK, and sets `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`. | `google/agents/cli/deploy/agent_runtime.py:137-138`; `scaffold/deployment_targets/agent_runtime/_shared/deployment/terraform/single-project/service.tf:57-64`; `scaffold/base_templates/python/…/app_utils/telemetry.py:28-33`, `:87-104`; `…/agent_runtime/python/…/fast_api_app.py:39-41`, `:85` |
| `vertexai` SDK directly: `client.agent_engines.create(config={"env_vars": {...}})` or `update`                               | Whatever you pass. If you omit the var, the SDK injects `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=unspecified`, with a docstring saying this exists "in order to achieve default-on telemetry".                                                                                                                                                                                                                                                                 | `vertexai/_genai/agent_engines.py:2355`, `:2398`; `vertexai/_genai/_agent_engines_utils.py:2156-2185`; legacy path `vertexai/agent_engines/_agent_engines.py:1172-1204`                                                                                                                            |
| Cloud Console toggle (console.cloud.google.com/vertex-ai/agents)                                                             | Presumably the same env var, server-side. ASSUMPTION: **not found** locally; known only from the deprecation text at `vertexai/adk.py:1005-1027`.                                                                                                                                                                                                                                                                                                                 |
| Legacy `AdkApp(enable_tracing=True)` in code (the BYOC container could do this)                                              | Overrides the env var per the truth table. Deprecated: the warning says it breaks the Console toggle.                                                                                                                                                                                                                                                                                                                                                             | `vertexai/adk.py:1005-1027`, `:1795-1815`                                                                                                                                                                                                                                                          |

**What `unspecified` means is the crux of the "automatic traces" question.**
Read literally by the wrapper it is None ⇒ tracing off. The SDK docstring says
it is there to get default-*on* telemetry, which only makes sense if the
platform resolves `unspecified` server-side (for example from the Console
toggle). Which of the two happens is **not found** in local code and needs the
Stage 5 control deploy. The `adk deploy agent_engine` path never produces
`unspecified` because it always passes `env_vars` through, so a control deploy
must use `adk deploy agent_engine` without the flag (env var absent ⇒ the SDK
injects `unspecified`).

Docs: docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/tracing
says set `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY: "true"` (optionally
`OTEL_SEMCONV_STABILITY_OPT_IN: gen_ai_latest_experimental` and
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT: EVENT_ONLY`), enable the
Telemetry API, and treats `enable_tracing` as legacy. The logging page gives
resource `aiplatform.googleapis.com/ReasoningEngine`, log ids
`reasoning_engine_stdout` / `reasoning_engine_stderr`, and `trace`/`span`
fields for correlation. ASSUMPTION: the class the service instantiates
server-side for an `adk deploy agent_engine` deploy is the `vertexai` `AdkApp`
template read here; the server-side wrapper is **not found** locally.

`OTEL_EXPORTER_OTLP_*` on Agent Runtime: with the native `AdkApp` wrapper nothing
calls `maybe_set_otel_providers`, so the Q1 limit applies and those vars do
nothing. ASSUMPTION, consistent with Q1 but not run.
- What ADK changes when it detects `GOOGLE_CLOUD_AGENT_ENGINE_ID`: telemetry
  schema **v2** (root span becomes `invoke_workflow {root}` instead of
  `invocation`, `_schema_version.py:40-91`); resource gains
  `cloud.platform=gcp.agent_engine`, `service.name=<engine id>`,
  `cloud.resource_id` (`google_cloud.py:get_gcp_resource`); logs exporter
  writes structured JSON to stdout with default log name `adk-on-agent-engine`
  (`google_cloud.py:_get_agent_engine_logs_exporter`, env `GCP_DEFAULT_LOG_NAME`);
  metrics use a request-driven reader because background threads are CPU-starved
  between requests (`adk/telemetry/_agent_engine_metric_exporter.py` docstring);
  trace context is taken from `Google-Agent-Engine-Traceparent`
  (`_agent_engine.py`). Which of ADK's or `vertexai`'s exporter set actually runs
  on a native deploy: **not found** locally; Stage 5 reads it back.

**Existing tutorial claim that the research contradicts.**
`tutorial/06-agent-runtime.md:16-18` and `deploy/deploy_agent_engine.sh:73-74`
say traces appear in Cloud Trace *automatically* and the flag only adds logs and
metrics. The truth table says default-off. The tutorial's own deploys always
passed `--otel_to_cloud`, so the "automatic" case was never exercised. Stage 1
rewrites the claim as unverified; Stage 5 tests it with a control deploy.

BYOC (`agent_runtime_byoc/main.py`): the container builds its own
`AdkApp(agent=root_agent)` (`main.py:56`), so the same env var governs it **if**
the deploy passes it; `deploy_byoc.py` passes only project/location/log-level
env vars today (`deploy_byoc.py:48-53`). `OTEL_EXPORTER_OTLP_*` alone does
nothing there (same Q1 limit: nothing calls `maybe_set_otel_providers`). Out of
scope for this rewrite beyond a one-paragraph note (see Open questions).

### Q5. OTel spans vs. logging plugins vs. ADK-native logging

Three different relationships, and the tutorial should say which is which:

| Pair                                                                                        | Relationship                                                                                                                                                                                                                                                                                 | Evidence                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python `logging` (streams 1–3) ↔ OTel spans/events                                          | **Independent.** No bridge into OTel; the CLI log format carries no trace or span id.                                                                                                                                                                                                        | No `LoggingHandler` in ADK (grep); `adk/cli/utils/logs.py:25-27`.                                                                                                                                                                                                     |
| `LoggingPlugin` / `DebugLoggingPlugin` ↔ OTel                                               | **Independent.** Neither imports OpenTelemetry; `LoggingPlugin` still `print()`s. They *run inside* the spans (before_model runs within `call_llm`), so a plugin *could* read the current span, but the built-ins don't.                                                                     | `adk/plugins/logging_plugin.py` (no otel imports; `:293` print), `debug_logging_plugin.py` (none); `base_llm_flow.py:1732-1736`. Contrast: `BigQueryAgentAnalyticsPlugin` inherits the ambient `trace_id` (`adk/plugins/bigquery_agent_analytics_plugin.py:825-860`). |
| OTel GenAI log events ↔ OTel spans                                                          | **Correlated automatically.** The OTel API stamps `trace_id`/`span_id` from the current span on every emitted LogRecord; the Cloud Logging exporter writes them as `logging.googleapis.com/trace` and `spanId`, and picks the log name from the event name, hence `gen_ai.user.message` etc. | `otel-sdk/opentelemetry/_logs/_internal/__init__.py:107-115`; `gcp-logging/opentelemetry/exporter/cloud_logging/__init__.py:324-331`, `:364-367`, `:417-421`.                                                                                                         |
| Part 4's `logging.googleapis.com/trace` (from `X-Cloud-Trace-Context`) ↔ OTel span trace id | **Different trace ids.** ADK never extracts Cloud Run's header into OTel context, so the JSON logs and the spans do not join in Cloud Trace.                                                                                                                                                 | `fast_api.py:531-547` handles only `Google-Agent-Engine-Traceparent`.                                                                                                                                                                                                 |

Duplication: with defaults, one prompt can appear in up to four places at once:
`google_adk` DEBUG lines (Part 1), `LoggingPlugin` output (Part 3), the span
attribute `gcp.vertex.agent.llm_request` (on by default via
`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`, `context.py:108-113`, `tracing.py:629-635`),
and `gen_ai.*` events when capture is enabled. Hand-join key: `LoggingPlugin`
prints `Invocation ID` (`logging_plugin.py:79,99,137,152,164`) and spans carry
`gcp.vertex.agent.invocation_id` (`tracing.py:622,744`) and
`gen_ai.conversation.id` = session id (`tracing.py:229,778`).

**Second existing claim the research contradicts.** `tutorial/05-otel.md:76-83`
warns that nothing short of a custom span processor strips the vendor
`llm_request`/`llm_response` attributes. `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`
does exactly that, and `adk deploy agent_engine --otel_to_cloud` sets it for
you. Stage 1 fixes this.

**Third existing claim the research contradicts.** `tutorial/05-otel.md:70-71`
and `examples/08_otel_cloud.py:35` say the content knob "must be set before ADK
is imported". In 2.8.0 both knobs are read when an invocation constructs its
`TelemetryConfig` (`tracing.py:865-873`; readers at `context.py:93-113`, called
from `:179-180`), so they take effect for the next turn and can live in the
agent's `.env`, unlike the exporter endpoint vars (Q1). Stage 1 fixes the
sentence; 5.6 relies on it for the knob demo.

Not found: any statement in ADK docs about how OTel log records relate to Python
logging (adk.dev/observability/logging/ does not address it).

---

## Scope

**In scope**

| File                                                           | Role in this rewrite                                                                                                                                                    |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ai/adk/logging/tutorial/05-otel.md`                           | Rewritten top to bottom (Stages 2–4, 6, 7).                                                                                                                             |
| `ai/adk/logging/tutorial/06-agent-runtime.md`                  | Telemetry paragraphs rewritten (Stages 1, 5).                                                                                                                           |
| `ai/adk/logging/tutorial/07-how-to-choose.md`                  | Decision-table rows, "Beyond logging", Verification status, References (Stages 1, 5, 6, 8).                                                                             |
| `ai/adk/logging/TUTORIAL.md`                                   | Contents row for Part 5; stream-4 "lands in" label (Stage 8).                                                                                                           |
| `ai/adk/logging/README.md`                                     | Files table rows for example 08 and new `otel/` assets (Stage 8).                                                                                                       |
| ~~`ai/adk/logging/examples/08_otel_cloud.py`~~ → `08_otel_server.py` | **Renamed and rewritten (Stage 4, 2026-09-05).** No longer an InMemoryRunner script; it is a minimal FastAPI OTel **server** (App + Runner + lifespan + `/chat`) whose only telemetry lines are `get_gcp_exporters(enable_cloud_logging=True)` + `maybe_set_otel_providers([hooks])`. Logging-only, no tracing, no console mode. |
| `ai/adk/logging/deploy/Dockerfile.otel_server` (new, Stage 4)  | Container for `08_otel_server.py`, following the `deploy/Dockerfile` (06 custom-server) pattern; `CMD python examples/08_otel_server.py`, no `.env` baked in (knob set via `--set-env-vars`). Used by 5.5's inline Cloud Run deploy. |
| `ai/adk/logging/deploy/deploy_agent_engine.sh`                 | Comment block lines 73–74 corrected (Stage 1); no behavior change.                                                                                                      |
| `ai/adk/logging/requirements.txt`                              | **DONE:** `google-adk[otel-gcp]>=2.8.0` adopted, plus `opentelemetry-exporter-otlp-proto-http` and `opentelemetry-exporter-gcp-logging`. No `OTEL_*` example vars in either env file: 5.7 shows them inline as prose. |
| `ai/adk/logging/demo_agent/requirements.txt`                   | Carries the container deps for `adk deploy cloud_run --otel_to_cloud` (the recorded boot-crash fix), including the `[otel-gcp]` extra. **DONE.** |
| ~~`ai/adk/logging/deploy/deploy_otel_cloudrun.sh`~~ (dropped)  | Superseded: 5.4 is inline copy-paste commands, not a wrapper script (Jeff's call). The script was created then deleted; the `adk deploy cloud_run` command lives in the tutorial directly. |
| `ai/adk/logging/otel/check_local.sh` (new, Stage 2)            | The one automated check: runs `adk api_server` with nothing configured and asserts span names via the debug endpoint.                                                   |
| `ai/adk/logging/CLAUDE.md`                                     | Only if a new convention is needed (e.g., "What you are looking at" callout label).                                                                                     |

**Out of scope**: the ADK and vertexai SDKs; tutorial Parts 1–4 except
cross-references; the four-streams framing; `agent_runtime_byoc/` (one
paragraph pointer only); the Part 4 custom server's Cloud Run deploy; running
anything against a non-Google backend (Jeff's call, 2026-09-04: Google Cloud is
the run target everywhere; other backends appear as one snippet in 5.5 and a
reference section in 5.7); modifying `06_custom_server.py` (5.5 says where the
two calls would go, but the runnable is example 08); any docs-site build (there is none, the tutorial is
GitHub-rendered Markdown; no `.github/workflows` exist).

---

## Target shape of Part 5

```
# Part 5 · OpenTelemetry
5.0  What stream 4 is, in one diagram (agent → in-process exporters, or → telemetry.googleapis.com / Cloud Logging); the five span names.
5.1  Nothing configured: `adk web` already traces. The Trace tab in the `adk web` UI. In memory, per process, gone on restart.
5.2  `adk web --otel_to_cloud`, locally: the required shell exports (`OTEL_RESOURCE_ATTRIBUTES` for the metrics 400, `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`), why they must be exports not `.env`, one turn entered in the UI, the `gen_ai.*` events in Logs Explorer with `<elided>` content, then the **event** content knob (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`) turning log content on, read back in Logs Explorer. **AS SHIPPED, 5.2 also opens Trace Explorer** and demos the **span** knob (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` → `llm_request`/`llm_response` = `{}` on the span while the logs keep content) — i.e. the two-independent-knobs lesson happens live in 5.2, not deferred to 5.6. ADC, APIs, roles, [otel-gcp] extras. Read-back is Logs Explorer with one Trace Explorer check for the span knob.
5.3  `adk api_server --otel_to_cloud`, locally then Cloud Run: the same exports (content off, `NO_CONTENT`), curl-driven, read through Cloud Logging; then `adk deploy cloud_run --otel_to_cloud`, curl the service, read the same back.
5.4  `adk deploy cloud_run --otel_to_cloud`, inline commands (no wrapper script): deploy, curl the service, read the `gen_ai.*` events in Logs Explorer (NOT Cloud Trace — this is the logging tutorial). Two traps in one collapsed aside (adk deploy exits 0 on failure; the [otel-gcp] boot-crash). `.env` ships in the image; `GOOGLE_CLOUD_LOCATION` repeated in --set-env-vars to beat the Dockerfile ENV.
5.5  Your own server: a minimal FastAPI OTel server (`08_otel_server.py`, a stripped 06_custom_server.py) that installs the Cloud Logging exporter itself — the two calls. Run locally, curl, read `gen_ai.*` in Logs Explorer; `.env` content-knob before/after (all OTEL_* vars work in `.env` here, unlike 5.2's CLI, because the server loads `.env` before building the exporters); then deploy to Cloud Run with inline `gcloud run deploy --source` (knob via --set-env-vars, no baked .env). A second, non-runnable snippet shows the OTLP variant for another backend.
5.6  The two content knobs as reference (spans vs events, turning content on deliberately, RunConfig scoping). No console-exporter aside (cut: it was a span exporter, off-topic for a logging tutorial).
5.7  Other backends, reference only: the generic OTLP env vars for CLI-launched servers (shell env, not `.env`), headers for vendor auth, http/protobuf only, and where the adk.dev integrations list is. No Docker, nothing run.
5.8  How this relates to Parts 1–4: one turn, four places; independent / correlated / duplicated
```

## Target shape of Part 6 (telemetry subsections)

Part 6 keeps its opening and its log read-back. Its current telemetry bullets
(`06-agent-runtime.md:12-23`) become four numbered subsections so the stage
headings below can refer to them the same way Part 5's do.

```
# Part 6 · Agent Runtime
6.1  One switch, two ways to set it: `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` on the deployment. The `--otel_to_cloud` flag writes it; a line in the agent's `.env` writes it too. What each way does and does not set (the flag also sets the span knob to false; `.env` does not). Setting neither = the platform decides (Console toggle); do not rely on it. One sentence on BYOC: the same env var governs a custom container's `AdkApp` if your deploy passes it (not run here).
6.2  Deploy A, the flag: `deploy_agent_engine.sh` as today. Read back Cloud Trace (root span name, `service.name` = engine id), Cloud Logging on the ReasoningEngine resource, and the deployment's env list showing the two vars the CLI added. The `llm_request` attribute is `{}` because the flag set it.
6.3  Deploy B, env vars only: same script with `ENABLE_VIA_ENV=1` (writes `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` and, explicitly, both knobs at their safe values into `demo_agent/.env`, no flag). Read back the same three things. The content-knob lesson for Agent Runtime: the span knob must be set by you on this route; with it unset the prompt lands in Cloud Trace. Shown by reading the env list, not by a third deploy.
6.4  What the platform changes: schema v2 root `invoke_workflow`, `cloud.platform=gcp.agent_engine`, `service.name`, log name, request-driven metrics. Only items the 6.2/6.3 read-backs actually showed.
```

Diagram budget (Mermaid, matching the existing parts): 5.0 flow and 5.8 the
four-places picture. 5.1–5.7 need none (the flow is 5.0's; 5.5 is a
two-destination variant of it, stated in prose).

---

## Stages

Each stage leaves the docs coherent if we stop after it. "M" = mechanical,
"J" = judgment-heavy.

### Stage 1 · Correct the three wrong claims in place (J, small)

- Goal: stop teaching three things the code contradicts, before any restructuring.
- Problems: P4 (partial), P8 (partial).
- Files: `tutorial/05-otel.md:68-83`, `tutorial/06-agent-runtime.md:12-18`,
  `deploy/deploy_agent_engine.sh:73-74`, `examples/08_otel_cloud.py:35,53-54` (docstring and `setdefault` comment), `tutorial/07-how-to-choose.md` (verification status: mark the "automatic traces" claim unverified).
- Steps:
  - [x] Replace the 05 WARNING with: `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` strips the vendor attributes; `adk deploy agent_engine --otel_to_cloud` sets it for you; span processor is the fallback for other attributes. **Done** (this session): rewritten in `tutorial/05-otel.md` with citations `telemetry/context.py:107-113`, `telemetry/tracing.py:629-635`/`:660-676`, `cli/cli_deploy.py:1281-1282`.
  - [x] Drop "must be set **before ADK is imported**" (05-otel.md:70-71) and the matching sentence in example 08's docstring. In 2.8.0 the knob is read when each invocation builds its `TelemetryConfig` (`tracing.py:865-873`, `context.py:179-180`), so it can be set any time before the turn, including in `demo_agent/.env`. ASSUMPTION: no import-time cache remains elsewhere; `grep -n "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT" adk/` shows only the `context.py`/`_stable_semconv.py` readers and a re-export in `tracing.py:90`. **Done** (this session): dropped from `05-otel.md` and both spots in `examples/08_otel_cloud.py` (docstring + comment). ASSUMPTION confirmed by the grep at `context.py:42-46,94-110`, `_stable_semconv.py:46`, `tracing.py:90,100,148`.
  - [x] Rewrite the 06 bullet as: telemetry is governed by `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`; the flag sets it, or a `.env` line does; if you set neither the platform decides, so set it explicitly. **Done** (this session): `tutorial/06-agent-runtime.md` bullet rewritten with `cli/cli_deploy.py:1273-1280`/`:1283-1291` citations.
  - [x] Same correction in the script's heredoc. **Done** (this session): `deploy/deploy_agent_engine.sh` heredoc rewritten.
  - [x] `07-how-to-choose.md` verification status: the "automatic traces" Agent Runtime claim marked unverified. **Done** (this session).
- Verify: `grep -n "automatically" tutorial/06-agent-runtime.md deploy/deploy_agent_engine.sh` has no telemetry hit; prose review. **PASS** (this session): grep returns nothing.

### Stage 2 · New Part 5 opening, 5.1 zero-config Trace tab, 5.2 `adk web --otel_to_cloud` (J) — DONE (Jeff, runs verified)

- Goal: a reader sees that `adk web` already traces with nothing configured, then adds one flag and finds the same run in Cloud Trace, Cloud Logging, and Cloud Monitoring, without writing code.
- Problems: P1, P3, P5 (cut), P7.
- Files: `tutorial/05-otel.md` (5.0, 5.1, 5.2), `requirements.txt` (add `opentelemetry-instrumentation-google-genai` via `google-adk[otel-gcp]`, see open question 3).
- Content decisions to make while writing:
  - 5.1 runs plain `adk web`, one turn, then the Trace tab **in the `adk web` UI** (Jeff, 2026-09-04: read the spans back by browsing the UI, not curl or the debug endpoint). Sample output = the span tree the Trace tab shows. State the three facts that motivate the rest of the part: a real provider is always installed (`api_server.py:649-666`), the exporters write to process memory (`api_server.py:458-518`), and nothing leaves the process. (The `/dev/.../debug/trace` endpoints exist under `adk web` but are not shown to the reader; `otel/check_local.sh` uses them for the automated check only.)
  - 5.2 is `adk web --otel_to_cloud ./`. (Original 2026-09-04 decision: read entirely through Cloud Logging, traces deferred to 5.3+. **SUPERSEDED as shipped:** 5.2's main read-back is Logs Explorer, but it also opens Trace Explorer once to demo the span knob — see Stage 2 span-knob note above.) The flow, in order:
    1. Before starting the server, export two shell vars (they cannot go in `.env`; see the timing callout below):
       - `OTEL_RESOURCE_ATTRIBUTES="service.instance.id=laptop-1,cloud.region=us-central1"` — **purpose: avoid the metrics 400.** `telemetry.googleapis.com/v1/metrics` maps the OTLP metric to the `prometheus_target` monitored resource, which requires a `service.instance.id` and a real `cloud.region`; `get_gcp_resource(project)` sets neither on a laptop, so without this every metric batch is rejected with `Failed to export metrics batch code: 400` (session finding; spans and logs export fine without it). State plainly that this is a laptop-only workaround: on Cloud Run / Agent Runtime the resource detector supplies region + instance.
       - `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` — the stable-semconv opt-in the tutorial's main path uses (matches the Agent Runtime docs page).
    2. Start `adk web --otel_to_cloud ./`, create a session and enter the London turn **in the UI** (not curl).
    3. Read the `gen_ai.*` events in the Cloud **Log Explorer**: content is `<elided>` because `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` defaults to `NO_CONTENT` (`context.py:93-105`). Note the aligned `trace`/`spanId` fields on the entries. Sample output = one `gen_ai.user.message` / `gen_ai.choice` pair with `<elided>`.
    4. Stop the server, `export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY`, restart, **new session**, repeat the turn, look in Log Explorer again: the message content is now present. Sample output = the same events with the prompt text. State the rule: with the experimental opt-in, `EVENT_ONLY` is the value that puts content in the log events; in production keep content off unless you have a reviewed reason (5.6 has the full knob table).
  - Why the vars must be shell exports, not `.env` (callout, stated once here): `adk web` builds the telemetry exporters at server construction (`api_server.py:1173`), before the agent's `.env` is loaded lazily on first agent load (`agent_loader.py:331-332`). This is the Q1 timing finding. Point forward to 5.7 for the general env-var mechanism.
  - Prerequisites stated once, here: ADC (`gcloud auth application-default login`), project from ADC or the shell's `GOOGLE_CLOUD_PROJECT` (not `.env`, which is not loaded yet), Telemetry API enabled, roles — `roles/telemetry.writer` covers all three (traces, metrics, logs), or the granular `cloudtrace.agent` + `logging.logWriter` + `monitoring.metricWriter` (session finding, my ADC identity was owner so not exercised as a minimal set), and the two exporter packages already in `requirements.txt`.
  - Explain the startup WARNING about the GenAI instrumentor and what `[otel-gcp]` adds. ASSUMPTION: installing it does not double the `generate_content` span (ADK has no suppression logic, grep found none). Verify in the run; if it duplicates, document and keep it out of `requirements.txt`. **NEEDS-RUN** (open question 5).
  - **REVISED (as shipped):** the span-attribute knob (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS`) **IS** demoed here, contrary to the original plan. 5.2 Step 2 turns the **event** knob on and checks Trace Explorer (content landed on the spans too); Step 3 sets `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` and shows in Trace Explorer that the span's `llm_request`/`llm_response` go `{}` while the logs still carry content — the "two independent knobs" lesson, live. 5.6 keeps the reference table but the live demo is here. Its safe value (`false`) is still what `adk deploy agent_engine --otel_to_cloud` sets for you (6.2).
- Verify: see Verification, Stage 2.

### Stage 3a · 5.3 `adk api_server --otel_to_cloud` locally (M) — DONE (Jeff, runs verified)

- Goal: the same flag on the headless server.
- Problems: P2, P3, P7.
- Files: `tutorial/05-otel.md` (5.3).
- 5.3 is mechanical (Jeff, 2026-09-04): before starting `adk api_server`, export the three vars — `OTEL_RESOURCE_ATTRIBUTES="service.instance.id=laptop-1,cloud.region=us-central1"` (same metrics-400 reason as 5.2), `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`, and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT` (content off is the production default; 5.2 already showed content on). Then reuse 1.3's curl block against the local server and read the `gen_ai.*` events back through Cloud **Logging** (say Cloud Trace / Monitoring are identical to 5.2's path). State the shared code path in one sentence with the citation (`fast_api_common_options`; `api_server.py:1173`). The `<elided>` content confirms `NO_CONTENT` took effect.
- Verify: see Verification, Stage 3 (5.3 row). **PASS** (Jeff, runs verified).

### Stage 3b · 5.4 `adk deploy cloud_run --otel_to_cloud` (J) — DONE (Jeff, runs verified)

- Goal: the same flag shipped to Cloud Run.
- Problems: P2, P3, P7.
- Files: `tutorial/05-otel.md` (5.4), `demo_agent/requirements.txt` (extras if adopted), `07-how-to-choose.md` (the `adk deploy cloud_run` traps note moves here from wherever the merge put it). **Update (later pass):** a wrapper script `deploy/deploy_otel_cloudrun.sh` was written then dropped — 5.4 is inline copy-paste commands (Jeff's call). See build note at top.
- 5.4 content (as shipped, 2026-09-05): four inline steps — deploy with `adk deploy cloud_run --otel_to_cloud ./demo_agent`, curl the service (URL fetched via `gcloud run services describe ... --format='value(status.url)'`), read the `gen_ai.*` events in **Logs Explorer** (NOT Cloud Trace — this is the logging tutorial), teardown. On Cloud Run the events land on a `generic_task` resource whose `job` is the service name. `demo_agent/.env` ships in the image (so `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` is carried, mentioned in passing). `GOOGLE_CLOUD_LOCATION=global` is repeated in `--set-env-vars` to beat the Dockerfile's `ENV GOOGLE_CLOUD_LOCATION=<region>` (`cli/cli_deploy.py:193`), explained in a `.env`-ships-in-image aside. Only **two** traps kept, in one collapsed aside: `adk deploy` exits 0 on failure (read the build output), and the `[otel-gcp]` boot-crash (`google_cloud.py:272`) that `demo_agent/requirements.txt` already prevents. CUT from the earlier draft: the Cloud Trace read-back, the `CMD`-line demonstration, the `--log_level` trap, and the Ready-check / Dockerfile-copier machinery (those lived in the deleted wrapper script; the reader now runs the command and sees gcloud's own output).
- Verify: see Verification, Stage 3 (5.4 row). **PASS** (Jeff, deploy run verified;
  see `07-how-to-choose.md` §Verification). Prose in `05-otel.md` §5.4.

### Stage 4 · 5.5 your own server, and 5.6 the content knobs (J) — DONE

- Goal: make explicit the one situation that needs code (your own server), and which knob controls prompt text where.
- Problems: P3 (the exception, made explicit), P6 (snippet half), P7, P8 (knob half). (P5 no longer touched here — the console aside was cut entirely.)
- Files: `tutorial/05-otel.md` (5.5, 5.6); `examples/08_otel_server.py` (renamed from `08_otel_cloud.py`, rewritten as a minimal FastAPI OTel **server**); `deploy/Dockerfile.otel_server` (new); `README.md`, `07-how-to-choose.md` references.
- **REDESIGNED 2026-09-05 — full design in `docs/adk-otel-5.5-redesign.md`.** 5.5 is a **minimal agent server you write**, not a fire-one-turn script. A stripped `06_custom_server.py`: `App` + `Runner` in a `lifespan` + `/chat` + `uvicorn.run`, whose only added telemetry is the two calls `get_gcp_exporters(enable_cloud_logging=True)` + `maybe_set_otel_providers([hooks])` (logging-only; no `get_gcp_resource` — that was a spans concern; no tracing; no console mode). Flow: (1) run locally, curl `/chat`, read `gen_ai.*` in Logs Explorer (resource `job` = `OTEL_SERVICE_NAME`); (2) **content knob before/after via `.env`** — `=true` shows text, `NO_CONTENT` shows `<elided>`; (3) deploy to Cloud Run with inline `gcloud run deploy --source` (Dockerfile copied to `./Dockerfile`, knob via `--set-env-vars`, no baked `.env`). Teaching point: on your own server **all** `OTEL_*` vars work in `.env`, unlike 5.2's CLI, because the server loads `.env` (`bootstrap()`) before building the exporters.
- 5.5 second snippet, labeled "not run here": the same shape for any OTLP backend, `maybe_set_otel_providers()` with the `OTEL_EXPORTER_OTLP_ENDPOINT`/`_HEADERS` vars set in the environment before the call (`setup.py:45-74`, `:124-147`). One sentence: same provider, different exporter, http/protobuf only. Point to 5.7.
- 5.6 is reference, not a run (the demo happened in 5.2 and 5.5): the two-knob table (span attributes vs log events, defaults, safe values), how to turn content **on** deliberately (`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY` / `SPAN_ONLY` / `SPAN_AND_EVENT`, `context.py:93-105`), `RunConfig.telemetry` for per-request scoping (`run_config.py:249-255`), and that `adk deploy agent_engine --otel_to_cloud` flips the span knob for you (`cli_deploy.py:1281-1282`). **No console-exporter aside** (cut 2026-09-05: span exporter, off-topic for a logging tutorial).
- Verify: **5.5 local runs VERIFIED LIVE** (Jeff's machine, 2026-09-05, `jwd-gcp-demos`): server starts, `/chat` returns a weather answer, `gen_ai.*` events land in Cloud Logging on a `generic_task` resource (`resource.labels.job` = `OTEL_SERVICE_NAME`), content knob confirmed both ways (`=true` → text; `NO_CONTENT` → `<elided>`). `08_otel_server.py` `py_compile` passes. **5.5's Cloud Run deploy is NEEDS-RUN** — inline commands + `deploy/Dockerfile.otel_server` written, not yet deployed; Step 4 carries no fabricated sample output (per CLAUDE.md).

### Stage 5 · 6.1–6.4 Telemetry on Agent Runtime (J) — DONE (2026-09-05, two live deploys)

- Goal: the reader knows the one switch, sees both ways of setting it work, and sees that the content knobs are set for them on one route and not on the other.
- Problems: P4, P7, P8 (knobs on Agent Runtime).
- Files touched: `tutorial/06-agent-runtime.md` (6.1–6.4 written), `deploy/deploy_agent_engine.sh` (`ENABLE_VIA_ENV` branch added; **also fixed** to call `./.venv/bin/adk`, it was resolving PATH to the sibling `ai/adk/.venv` = 2.5.0/py3.14), `07-how-to-choose.md` (verification status).
- **AS BUILT (what actually happened, replacing the pre-run assumptions):**
  - 6.1: the switch (`GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY`, `vertexai/adk.py:1767-1815`), the two routes (flag sets it + the span knob `false`, `cli_deploy.py:1273-1282`; `.env` line sets only itself, `:1283-1291`), the `unspecified`/"platform decides, set it explicitly" note, and a BYOC one-liner. Written as prose from citations.
  - 6.2 (flag) and 6.3 (`.env` route, `ENABLE_VIA_ENV=1`): **both deployed for real.** The read-back that WORKED is the deployment **env list**, read via the `vertexai` SDK — `engine.api_resource.spec.deployment_spec.env` (a list of `EnvVar(name,value)`). **`gcloud ai reasoning-engines` does NOT exist in this gcloud install** (the plan's assumed path is wrong); the SDK is the real path. 6.2's list shows `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true` + `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (both added by the CLI); 6.3's shows the three lines `.env` carried and nothing the CLI added. Both are real captures.
  - **KEY FINDING (verified negative, contradicts the earlier plan premise):** querying a telemetry-enabled deployed engine produced **NO `gen_ai.*` logs and NO Cloud Trace spans** — only `reasoning_engine_stderr` framework INFO lines. Tested with two control deploys, multiple queries, a 40-minute window. So 6.2/6.3 do NOT read `gen_ai.*` events back (unlike Cloud Run 5.4); Part 6 states only what surfaced (the framework logs + the env lists) and flags the telemetry-destination question OPEN in Part 7. This resolves part of Q4: the enablement vars are set correctly, but the OTel events do not appear where local/Cloud Run put them.
  - 6.4: the observed platform-differences table (the switch, who sets the knobs, `reasoning_engine_stderr` logs, and the "gen_ai.* did not surface" row).
- Cloud hygiene: both control engines deleted after the runs; a stray engine from the initial wrong-venv deploy also deleted; Jeff's two pre-existing engines untouched; temp folders removed; `demo_agent/.env` restored by the script trap.
- Verify: see Verification, Stage 5 (row updated to logging-first + the negative finding).

### Stage 6 · 5.7 Other backends, reference only (J, small) — DONE (2026-09-05)

- Goal: a reader who needs a non-Google backend knows the mechanism and its limits without the tutorial running one.
- Problems: P6.
- Files: `tutorial/05-otel.md` (5.7), `07-how-to-choose.md` (References).
- Content, all prose and one command block that is shown but not part of the run path: for CLI-launched servers the flag is replaced by env vars, honored when `--otel_to_cloud` is absent (`api_server.py:657-658`, `setup.py:124-147`); a four-row table of the vars (`OTEL_EXPORTER_OTLP_ENDPOINT` or the per-signal `_TRACES_`/`_METRICS_`/`_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS`, `OTEL_SERVICE_NAME`/`OTEL_RESOURCE_ATTRIBUTES`) with the opentelemetry.io defaults; **for CLI-launched servers these must be shell exports, not `.env`** (Q1 timing finding, cited) — but note the contrast established in 5.5: **on your own server they can live in `.env`** because the server loads `.env` before building the exporters. http/protobuf only (no gRPC exporter is imported); for your own server, point back to the 5.5 second snippet (`maybe_set_otel_providers()` no-arg). Close with the adk.dev integrations list (`/integrations/?topic=observability`) and the note that some vendors document a code path rather than env vars (MLflow is the example: `http://localhost:5000/v1/traces` with an `x-mlflow-experiment-id` header). Everything in this section is labeled "not run here". **This stage runs nothing — pure reference from code citations; safe to write without a live run.**
- Verify: see Verification, Stage 6.

### Stage 7 · 5.8 Logging interplay (J) — DONE (2026-09-05, verified live)

- Goal: one turn, seen in the four places at once, with the independent/correlated/duplicated table from Q5 and the join key.
- Problems: P8, P7.
- **REVISED (2026-09-05, session direction).** The four places are the four log/telemetry streams a reader has met: (1) `google_adk` DEBUG lines, (2) `LoggingPlugin` output, (3) the OTel span attribute `gcp.vertex.agent.llm_request`, (4) the `gen_ai.*` OTel log events. The section's own read-back stays in **Cloud Logging** for the OTel half (Logs Explorer, `logName=~"gen_ai\."`) and terminal stdout for the DEBUG + plugin half; the span attribute (place 3) is named and cited but the reader is NOT sent to Trace Explorer to hunt it (5.2 already showed the span knob live) — it appears as a row in the Q5 independent/correlated/duplicated table, not a live step. Keeps the section logging-centered.
- Files: `tutorial/05-otel.md` (5.8), `TUTORIAL.md` (stream-4 label), `07-how-to-choose.md` (best-practice bullets: which of the four to turn off in production).
- Runnable: simplest path that shows DEBUG + plugin + OTel export in one process. Prefer running a turn against the **5.5 server** (`08_otel_server.py`) with `LoggingPlugin` added and `google_adk` at DEBUG, over inventing a new agent module — but VERIFY what actually composes cleanly before committing to it (ASSUMPTION: `App(plugins=[LoggingPlugin()])` + DEBUG + the two OTel calls coexist). If a live run is not done this pass, write the Q5 table + join-key prose (fully supported by code citations) and mark the "four places" captured-output block NEEDS-RUN.
- The independent/correlated/duplicated content is Q5 (fully cited): Python logging ↔ OTel = independent; LoggingPlugin ↔ OTel = independent; `gen_ai.*` events ↔ spans = correlated (trace/span id stamped); Part 4 `X-Cloud-Trace-Context` trace ↔ OTel span trace = different ids. Join key: `Invocation ID` in plugin output = `gcp.vertex.agent.invocation_id` on spans = `gen_ai.conversation.id` (session id).
- Verify: see Verification, Stage 7.

### Stage 8 · Cross-references, tables, verification status, link check (M) — DONE (2026-09-05)

- Goal: index, README, decision table, references, and nav footers agree with the shipped Part 5/6.
- Problems: closes P7's "explains what you are looking at" for the index diagram.
- **REVISED (2026-09-05): line numbers below are stale (Part 5 grew); grep for the text, not the line.** Specific fixes known needed this session:
  - `TUTORIAL.md` Part 5 contents row currently says "GenAI **spans to Cloud Trace**, and the content-capture privacy knob" — Part 5 as shipped is logging-focused (reads back in Logs Explorer throughout, 5.2 the one Trace Explorer check). Reword toward "GenAI `gen_ai.*` events to Cloud Logging (traces/metrics also flow), and the content-capture privacy knob."
  - `TUTORIAL.md` stream-4 destination label → "Cloud Logging (`gen_ai.*`), plus Cloud Trace / Monitoring, or any OTLP collector".
  - `README.md` example-08 row is already updated to `08_otel_server.py` (done this session) — re-verify.
  - `07-how-to-choose.md`: decision-table rows for stream 4 / OTel; Verification status (already updated for 5.4/5.5 this session); References: add adk.dev/observability/traces|metrics|logging, the Agent Runtime tracing page, the OTel OTLP env-var page.
  - Any remaining `08_otel_cloud` / `deploy_otel_cloudrun.sh` references outside history (grep).
- Verify: `grep -rn -E "05-otel|Part 5|08_otel|08_otel_cloud|deploy_otel_cloudrun|Cloud Trace" ai/adk/logging` shows only intended hits; the `logName=~"gen_ai\."` Query-editor form is used everywhere; link check passes (see below).

---

## Verification

### Common harness

- Clean environment = fresh `python3.13 -m venv .venv && pip install -r requirements.txt`, `.env` from `.env.example`, `source env.sh`, Docker running. Every command is `ai/adk/logging/.venv/bin/...`.
- Prompt for all runs: "What's the weather in London?" so span/attribute values are stable across stages.
- Expected span names (schema v1, local): `invocation`, `invoke_agent weather_agent`, `call_llm` ×2, `generate_content gemini-3.7-flash` ×2, `execute_tool get_weather`. Expected attributes on `execute_tool`: `gen_ai.operation.name=execute_tool`, `gen_ai.tool.name=get_weather`, `gcp.vertex.agent.invocation_id` set. Expected events per LLM call: 1× `gen_ai.system.message`, ≥1× `gen_ai.user.message`, 1× `gen_ai.choice`.
- Proposed automated check (new file `otel/check_local.sh`, ~30 lines, needs no cloud): run plain `adk api_server` in the background, create session + POST `/run`, fetch `/dev/apps/demo_agent/debug/trace/session/{id}`, assert the span names above, tear down. Exit non-zero on a missing name. This exercises 5.1 and the shared code path; the Cloud read-backs in 5.2–5.4 stay manual (ADC and a project).
- Link check: `lychee --offline 'ai/adk/logging/**/*.md'` or an equivalent Python one-liner over relative links; no docs build exists.

### Per stage

| Stage | Must run from clean env                                                                                                           | Pass condition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Automated                                                         | Human                                                                                                                                                                                      | Not in CI, covered by                                                        |
| ----- | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| 1     | nothing                                                                                                                           | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | grep for "automatically"                                          | prose reads correctly; claim marked unverified                                                                                                                                             | n/a                                                                          |
| 2     | plain `adk web` + one turn (5.1); `adk web --otel_to_cloud` + one turn, then `export`ing the event knob and restart, then `export ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` + restart + one more turn (5.2) | 5.1: Trace tab and `/debug/trace/session/{id}` show the seven expected spans with no configuration; 5.2: `gen_ai.*` events in **Logs Explorer** (Query editor, `logName=~"gen_ai\."`) with `<elided>` then, after the event knob, with content; a **Trace Explorer** check shows `gcp.vertex.agent.llm_request` full while the event knob is on, then `{}` after `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (the two-independent-knobs demo, live in 5.2); startup WARNING text matches the doc | `otel/check_local.sh` for 5.1 (uses `api_server`, same code path) | reader sees traces before configuring anything, then the event knob and the span knob independently in Logs Explorer + Trace Explorer; Expected output matches the real payloads; 5.0 diagram matches the flow | 5.2 read-backs: recorded run + date in Verification status; re-run checklist |
| 3     | `adk api_server --otel_to_cloud` + curl (5.3); inline `adk deploy cloud_run --otel_to_cloud ./demo_agent`, curl, teardown (5.4)   | 5.3: `gen_ai.*` events in Logs Explorer (Query editor, `logName=~"gen_ai\."`), content `<elided>` (`NO_CONTENT`); 5.4: service reaches Ready, a `/run` turn (curl, the `api_server` route the CLI serves) returns a weather answer, `gen_ai.*` events land in **Logs Explorer** on a `generic_task` resource (`job` = service name). Read back is LOGS, not Cloud Trace. | none (inline commands; no wrapper script)                         | the two traps read as one aside; `gen_ai.*` events appear from the Cloud Run process; sample output from the real deploy                                                                    | the deploy: recorded run + date; teardown in the text                        |
| 4     | `08_otel_server.py` run locally + curl `/chat` + knob before/after (5.5); Cloud Run deploy of the same server (5.5 Step 4); nothing for 5.6 | 5.5 LOCAL (**verified live** 2026-09-05): server starts, `/chat` returns a weather answer, `gen_ai.*` events in Logs Explorer on a `generic_task` resource (`job` = `OTEL_SERVICE_NAME`), knob `=true` → text present, `NO_CONTENT` → `<elided>`. 5.5 CLOUD RUN (**NEEDS-RUN**): deploy reaches Ready, `/chat` works, `gen_ai.*` in Logs Explorer, content `<elided>` from `--set-env-vars`. The runnable file is a minimal server with only the two calls added; the OTLP snippet is prose-only, "not run here". | `py_compile examples/08_otel_server.py` (passes)                  | 5.5's framing is why code appears at all; the `.env`-works-here callout is the teaching point; 5.6's table matches `context.py:93-113` and the deploy default at `cli_deploy.py:1281-1282` | Cloud Run deploy: NEEDS-RUN; local runs recorded 2026-09-05                  |
| 5     | `deploy_agent_engine.sh` (flag, 6.2); `ENABLE_VIA_ENV=1 deploy_agent_engine.sh` (no flag, 6.3); one query each; delete both       | **DONE, two live deploys (2026-09-05).** Env lists read back via the `vertexai` SDK (`engine.api_resource.spec.deployment_spec.env`; `gcloud ai reasoning-engines` does NOT exist here): 6.2 = `…ENABLE_TELEMETRY=true` + `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` added by the CLI; 6.3 = the three lines `.env` carried and nothing CLI-added. **VERIFIED NEGATIVE:** the deployed engine produced NO `gen_ai.*` logs and NO Cloud Trace spans (only `reasoning_engine_stderr` framework INFO) over 40 min / multiple queries — so 6.2/6.3 read only the env lists + framework logs, and the telemetry destination is flagged OPEN. | `bash -n` on the script (passes) | the platform-differences list (6.4) contains only observed items; the two env lists in the text are the real captures; both control engines + a stray deleted; Jeff's pre-existing engines untouched | env lists + framework logs recorded 2026-09-05; the gen_ai.*/trace destination is an open question in Part 7 |
| 6     | nothing                                                                                                                           | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | link check on the opentelemetry.io and adk.dev URLs               | env-var table matches `setup.py:124-147` and the opentelemetry.io defaults; every block carries the "not run here" label; the `.env` timing claim cites the code                           | the whole section, by design; the code citations are the evidence            |
| 7     | `--log_level DEBUG` + `LoggingPlugin` + `--otel_to_cloud`, one turn                                                               | the same `Invocation ID` appears in plugin output and as `gcp.vertex.agent.invocation_id` on the spans; the DEBUG prompt text, the plugin's prompt text, and the span's `llm_request` are the same string; `gen_ai.*` events show `<elided>`                                                                                                                                                                                                                                                                               | none                                                              | the "four places" figure matches the captured output; the independent/correlated/duplicated table is stated per pair                                                                       | n/a                                                                          |
| 8     | nothing                                                                                                                           | links resolve; cross-ref grep clean                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | link check; grep                                                  | contents table and README rows read correctly                                                                                                                                              | n/a                                                                          |

---

## Open questions

### Decisions (all taken by Jeff, 2026-09-04)

1. ~~A third Agent Runtime deploy to record the default~~ **Skip.** 6.1 says "the platform decides when you set neither; set it explicitly" and claims no default.
2. ~~BYOC telemetry~~ **Out.** `deploy_byoc.py` is untouched; 6.1 carries one pointer sentence saying the same env var governs a BYOC container's `AdkApp` if the deploy passes it.
3. ~~Where the `adk deploy cloud_run` traps live~~ **Move into 5.4.** Stage 3 deletes the note from `07-how-to-choose.md` and Stage 8's cross-reference grep confirms nothing still points at it.

### Facts the runs will supply

No action from Jeff. Each is an ASSUMPTION in the stage text that the named run replaces with what was observed; the executor writes the observed value into the tutorial and strikes the item here.

4. ~~**Which exporter set runs on a native Agent Runtime deploy?**~~ **PARTIALLY RESOLVED (2026-09-05, two live control deploys).** The enablement env vars are set correctly by both routes (env lists in 6.2/6.3 prove it). But the expected OTel telemetry **did not surface at all**: no `gen_ai.*` logs under any log name, no `adk-on-agent-engine` log, and no Cloud Trace spans, across a 40-minute window and multiple queries of a telemetry-enabled engine. Only `reasoning_engine_stderr` (framework INFO) and `reasoning_engine_stdout` appeared. So the log-name/root-span/metrics sub-questions are moot until the prior question — *where does native Agent Runtime OTel telemetry go?* — is answered; it may need Console-side enablement or a path the SDK deploy does not trigger. Recorded as OPEN in Part 7's Verification status; Part 6 asserts only the framework logs + env lists.
5. **Does `google-adk[otel-gcp]` double the `generate_content` spans?** **NOT VERIFIED BY THIS SESSION (Fable 5.1, 2026-09-04).** The "No … runs 52m vs 52c" answer previously written here was added outside this session; I did not install the extra or run the comparison, so I cannot vouch for it. What I did establish: the dry-run install adds 7 packages (`opentelemetry-instrumentation{,-google-genai,-grpc,-httpx}`, `opentelemetry-util-{genai,http}`, `wrapt`), and without the extra the startup WARNING (`Unable to import GoogleGenAiSdkInstrumentor …`, `api_server.py:747`) fires and the plain-`adk web` run produced exactly one `generate_content` per `call_llm` (7 spans total). Whether installing the extra changes that count still needs a real before/after run. **NEEDS-RUN.**
6. **Metric type names in Cloud Monitoring**, the Cloud Run resource type on exported entries, the deployment env-list field path, and the exact IAM roles for the telemetry endpoint. Stages 2, 3 and 5 supply them.
   - **Deployment env-list field path (RESOLVED 2026-09-05):** the plan's `gcloud ai reasoning-engines describe` does **not** exist in this gcloud install. The working path is the `vertexai` SDK: `client.agent_engines.get(name=…).api_resource.spec.deployment_spec.env` → a list of `EnvVar(name, value)`. Used in 6.2/6.3.
   - **Cloud Run resource on exported `gen_ai.*` entries (RESOLVED 2026-09-05, 5.5 local + Cloud Run):** the OTel Cloud Logging exporter labels entries with a **`generic_task`** monitored resource whose `resource.labels.job` is the `OTEL_SERVICE_NAME` (not `service.name` — that trips up filters). Filter on `resource.labels.job` or the `logName=~"gen_ai\."` query.
   - **Metrics endpoint resource (observed this session, replaces the Stage 2 `workload.googleapis.com/` ASSUMPTION):** `telemetry.googleapis.com/v1/metrics` maps the OTLP metric to the **`prometheus_target`** monitored resource, so exported series appear as `prometheus.googleapis.com/gen_ai.*` (metric-type name not confirmed against a real agent run; the 200s I got used a synthetic point). Locally the export needs resource attributes ADK's `get_gcp_resource(project)` does not set on its own: a `service.instance.id` **and** a real `cloud.region` (e.g. `us-central1`; `global` is rejected: "location / region / zone label cannot be set to 'global'"). Supply them via `OTEL_RESOURCE_ATTRIBUTES` in the shell. Without them every metric batch returns 400 (`prometheus_target resource type must have an instance specified`, then `Unrecognized region or location`). **Spans and logs export fine without any of this.** On Cloud Run / Agent Engine the resource detector should supply region + instance, so this may be laptop-only — not confirmed by me.
   - **IAM roles for the telemetry endpoint (observed this session):** `roles/telemetry.writer` bundles all three needed permissions (`telemetry.traces.write`, `monitoring.timeSeries.create`, `logging.logEntries.create`); the granular equivalents are `cloudtrace.agent` (or `telemetry.tracesWriter`) for traces, `monitoring.metricWriter` for metrics, `logging.logWriter` for logs. My ADC identity is project owner, so these were not exercised as a minimal set.

### Resolved

7. ~~Which third-party target to run for real~~ Dropped (Jeff, 2026-09-04): no non-Google backend is run. If that changes later, MLflow is the cheapest self-hosted candidate (documented OTLP endpoint and header).
8. ~~Example 08's filename~~ **Renamed to `08_otel_server.py`** (2026-09-05): it is now a minimal FastAPI server, not a `cloud`/`console` mode script. Logging-only, no modes.
9. ~~Which file holds the `OTEL_*` vars~~ Resolved by code: `env.sh` (shell env). `adk web` loads the agent's `.env` only when the agent is first loaded, after telemetry setup has run (`agent_loader.py:331-332`, `api_server.py:1173`). Stated with the code citation in 5.7; not demonstrated by a run.
