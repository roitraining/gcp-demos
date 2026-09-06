# Rewrite the ADK OpenTelemetry tutorial (Part 5, Part 6 telemetry)

Folder: `ai/adk/logging/`. Status: **all stages done** (2026-09-05). Same day, 6.2/6.3 were reworked from a wrapper script to inline commands plus a canned env library, and 5.2/5.5 were corrected against live runs; see [Session log (2026-09-05)](#session-log-2026-09-05). Where a session-log entry conflicts with an older stage section, the session log wins.

Three items remain, none a blocker:

- 5.5's Cloud Run deploy of `08_otel_server.py` (NEEDS-RUN).
- 5.5 Step 3 under the experimental convention (NEEDS-RUN; the page's `<elided>` sentence predates the opt-in).
- Where native Agent Runtime OTel telemetry lands. Verified negative twice (2026-09-04 script deploys, 2026-09-05 inline 6.2 deploy): no `gen_ai.*` logs or traces surfaced. Open in the How to choose page.

## Reading this plan

**Paths.** The tutorial was split into one page per subtask after this plan completed. Stage and verification sections keep the old paths as history; the scope table uses the new ones. Old `:line` suffixes no longer resolve.

| Old path | New location |
|---|---|
| `tutorial/05-otel.md` (5.0–5.8) | `tutorial/part-5/index.md` + `tutorial/part-5/5.N-*.md` |
| `tutorial/06-agent-runtime.md` (6.1–6.4) | `tutorial/part-6/index.md` + `tutorial/part-6/6.N-*.md` |
| `tutorial/07-how-to-choose.md`, "Part 7" | `tutorial/how-to-choose.md` |

**Citations.** `adk/<path>:<line>` means `ai/adk/logging/.venv/lib/python3.13/site-packages/google/adk/<path>`. `vertexai/adk.py` means `.../site-packages/vertexai/agent_engines/templates/adk.py`. `otel-sdk/…` and `gcp-logging/…` are the installed OpenTelemetry packages. Line numbers are from the 2.8.0 install (research 2026-09-04: google-adk 2.8.0, google-cloud-aiplatform 2.1.0, opentelemetry-sdk 1.42.1, Python 3.13.3).

**Venv trap.** The sibling `ai/adk/.venv` holds google-adk 2.5.0 on Python 3.14 and is first on PATH in some shells. Every command here runs as `ai/adk/logging/.venv/bin/...`.

**Superseded docs.** `docs/adk-otel-5.5-redesign.md` and `docs/adk-logging-merge-parts-4-6.md` were deleted 2026-09-05. What still matters from the 5.5 redesign is in its Build decisions row and Stage 4; the Parts 4–6 merge is fully reflected in the tutorial.

## Build decisions (Jeff)

| Section | Decision |
|---|---|
| 5.4 | Inline copy-paste commands, no wrapper script. `deploy/deploy_otel_cloudrun.sh` was written, then deleted. Read-back is Logs Explorer, not Cloud Trace. Only two traps kept, in one aside: `adk deploy` exits 0 on failure, and the `[otel-gcp]` boot-crash. |
| 5.5 | Redesigned 2026-09-05 (design doc folded in here, then deleted). A minimal OTel **server** (`08_otel_server.py`, renamed from `08_otel_cloud.py`), logging-only: `bootstrap()` loads the **root** `.env` (`ai/adk/logging/.env`, not `demo_agent/.env`), then `get_gcp_exporters(enable_cloud_logging=True)` + `maybe_set_otel_providers([hooks])` before the `Runner`; a bare `POST /chat`; none of 06's formatter or trace-context code (stream 4 is 08's only added concern). Teaching point: local uses `.env`, Cloud Run uses `--set-env-vars`, same knob. Local run verified. Step 3 turns content off **and** opts into the experimental convention in one root-`.env` edit; Step 4's Cloud Run deploy passes the same opt-in. Cloud Run deploy is inline commands + `deploy/Dockerfile.otel_server` (no `.env` in the image), NEEDS-RUN. |
| 6.2 / 6.3 | Reworked 2026-09-05: no wrapper script. Each page copies a canned env file from `deploy/env/` into `demo_agent/.env`, runs `adk deploy agent_engine` inline (6.2 with `--otel_to_cloud`, 6.3 without), greps the engine id from the deploy output, reads the env list and the logs with inline SDK and `gcloud` commands, and restores `deploy/env/default.env`. Page titles unchanged. `deploy_agent_engine.sh` remains for 1.6 only. |
| `.agent_engine_config.json` | Considered for the 6.2/6.3 A/B (base config in `.env`, knobs in two config files) and rejected: a non-empty `.env` replaces the config file's `env_vars` wholesale. See Q4. |
| 5.6 | Console-exporter aside cut. It was a span exporter, off-topic for a logging tutorial. |
| Other backends | Nothing runs against a non-Google backend. One snippet in 5.5, a reference section in 5.7. |

## Session log (2026-09-04, Fable 5.1)

Covers only what that session ran. Jeff executed and verified 5.1–5.4 separately.

**Environment.** adk 2.8.0, Python 3.13.3, port 8000 free, Docker 28.4.0. ADC project `jwd-gcp-demos`, identity `jeff@jwdavis.me` (owner). Telemetry, Trace, Logging, and Monitoring APIs enabled.

**Stage 1.** All four corrections applied. `grep -n "automatically"` on the two files returns nothing. `bash -n` passes on both scripts.

**Stage 2 findings.**

- **5.1 works with nothing configured.** Seven spans read back from `/dev/apps/demo_agent/debug/trace/session/{id}` (trace `3037b29d…`).
- **`check_local.sh` uses `adk web`, not `adk api_server`.** `api_server` installs the same in-memory exporters but registers no `/dev` debug routes (404 confirmed; `/openapi.json` lists none). Only `DevServer` mounts them (`cli/dev_server.py:463`, `:796-822`). This contradicts the original Q3 claim.
- **5.2 "before" state.** `adk web --otel_to_cloud` with no `[otel-gcp]` extra exported all 7 spans to Cloud Trace (trace `2d442bd3…`). `gen_ai.*` events landed in Cloud Logging with `<elided>` content and matching `trace`/`spanId`. Startup WARNING matched `api_server.py:747`. `call_llm` spans carried full `llm_request`/`llm_response`.
- **Metrics 400 diagnosed.** `telemetry.googleapis.com/v1/metrics` maps OTLP metrics to the `prometheus_target` resource, which needs `service.instance.id` and a real `cloud.region`. `get_gcp_resource(project)` sets neither on a laptop.

  | Resource attributes | Result |
  |---|---|
  | none | 400 `prometheus_target resource type must have an instance specified` |
  | `service.instance.id` only | 400 `Unrecognized region or location` |
  | `service.instance.id` + `cloud.region=us-central1` | 200 |
  | `cloud.region=global` | 400 `cannot be set to "global"` |

  `OTEL_RESOURCE_ATTRIBUTES=service.name=…,service.instance.id=…,cloud.region=us-central1` also works. Spans and logs export without any of this. Metric type names were not confirmed against a real agent run.
- **`[otel-gcp]` doubling** not tested. Dry-run install adds `opentelemetry-instrumentation-google-genai 0.7b1`, `-grpc`, `-httpx`, `opentelemetry-util-genai`, `wrapt`. NEEDS-RUN.

**Cloud writes.** Two local `adk web --otel_to_cloud` runs and a few synthetic metric points. No deploys.

## Session log (2026-09-05)

Jeff ran every command; the session edited pages and diagnosed against the installed source. Commits `6f0061b` (fixes, inline Part 6 deploys, env library) and `a09af74` (nav flip). Overrides the older stage sections where they differ.

**5.2.** The eight-entry prose was wrong. Real count for one turn, from a Logs Explorer export: two `gen_ai.system.message`, four `gen_ai.user.message`, two `gen_ai.choice`, across two `call_llm` spans. The first call logs 1 system + 1 user + 1 choice; the second replays the question, the `get_weather` call, and the tool response as three user messages, so 1 + 3 + 1. Every entry also carries `traceSampled: true`, which the Step 1 expected-output block omits. London prompt blocks added to Steps 2, 4, and 5.

**5.5.** Two fixes from a live run.

- The `.env` content knob "was not taking effect": `bootstrap()` loads the **root** `.env`, and `load_dotenv` never overrides a variable already in the shell. A leftover `export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT` from 5.2 was winning. Step 1 now starts with `unset` of that var. Diagnostic: `.venv/bin/python -c "from examples._common import bootstrap; bootstrap(); import os; print(os.getenv('OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT'))"`; if it disagrees with `.env`, a shell export is shadowing it. Both code paths accept `true` (ADK maps truthy to `EVENT_ONLY`, `context.py:93-104`; the `google_genai` instrumentor compares `.lower() == "true"`, `flags.py:26-33`), so the value was never the problem.
- Step 3 is one root-`.env` edit with two assignments (`NO_CONTENT` and `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`), the `true` line commented out, followed by an explicit restart, re-curl, and re-query. Step 4's `--set-env-vars` carries the same opt-in. Not yet re-run: under the experimental convention with `NO_CONTENT` the consolidated event simply lacks content (5.2 Step 4), so Step 3's "reads `<elided>`" sentence needs confirming or rewording.

**6.2 / 6.3.** Rewritten to inline commands and a canned env library: `deploy/env/default.env`, `6.2a.env` (identical to default; base config only, the flag supplies telemetry), `6.2b.env` (adds `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`, `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`, `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`). No `GOOGLE_CLOUD_PROJECT` in any of them; `--project` supplies it and the CLI pops it from `.env` anyway. The repo `.gitignore`'s `env/` and `.env` rules caught the directory, so a negation for `ai/adk/logging/deploy/env/` was added. Two bugs found live:

- The SDK heredocs used a quoted delimiter (`<<'PY'`) with `$GOOGLE_CLOUD_PROJECT`/`$REGION` inside, so the strings reached Python unexpanded (`certificate is not valid for '$region-aiplatform.googleapis.com'`). Fixed by passing project, region, and engine id as argv and reading `sys.argv`. 1.6's heredocs use an unquoted `<<PY` and were never affected.
- `gcloud logging read` right after the query returned nothing; Agent Runtime logs lag ingestion. A `sleep 15` now precedes the read. An inline `#` comment in the pasted block broke zsh (`command not found: #`), so blocks carry no comments; the explanation is in the prose.

6.2 re-run end to end with the inline commands. The read returned `reasoning_engine_stderr` INFO lines, framework `UserWarning`/`FutureWarning` lines (Python warnings on stderr, logged at INFO; harmless), and one `reasoning_engine_stdout` uvicorn access line. 617 entries on the engine, none `gen_ai.*`. The verified negative stands. The expected-output block keeps the three clean INFO lines; a message-first `--format` was tried and reverted. 6.3 is now self-contained (its own env-list read, query, and log read against `$ENGINE_ID_ENV`) instead of "same command as 6.2". 6.2's Deep dive explains the copy/restore, not the script. The reader restores `demo_agent/.env` with `cp deploy/env/default.env demo_agent/.env`; there is no trap.

**`.agent_engine_config.json`.** Investigated as a way to hold the 6.2/6.3 knobs while `.env` keeps the base config. Rejected; the merge rule is in Q4.

**Out of plan, same session.** 4.3's Cloud Run read now adds `jsonPayload.message:*` to the query: plain-format `textPayload` rows from uvicorn, ADK internals, and `agent.py` rendered as blank `MESSAGE` cells, and the old expected output showed two of them as if they had a `jsonPayload.message`. Every tutorial page's nav block now lists back before next (34 pages, 68 blocks); `ai/adk/logging/CLAUDE.md` still describes the old nav shape.

## Coverage

| # | Problem | Resolved by | How we know |
|---|---|---|---|
| P1 | No `adk web` OTel switch/env-var coverage | Stage 2 | 5.1 shows the Trace tab with nothing configured. 5.2 runs `--otel_to_cloud` and reads `gen_ai.*` in Logs Explorer, plus one Trace Explorer check for the span knob. States that no `.env` var enables Cloud export and `OTEL_*` vars must be shell exports. |
| P2 | Same gap for `adk api_server` | Stage 3 | 5.3 repeats 5.2 with `api_server` and curl; names the shared code path. 5.4 ships the flag to Cloud Run. |
| P3 | Readers write unnecessary OTel config code | Stages 2–4 | 5.1–5.4 use zero agent code. 5.5 is the one place code appears and says why: your own server must make the two calls the CLI would have made. |
| P4 | Agent Runtime telemetry not addressed | Stage 5 | 6.1 names the one switch and two routes. 6.2 and 6.3 deploy each route and read back the env list. "Traces appear automatically" is replaced by "the platform decides when you set neither; set it explicitly." |
| P5 | Console span output as primary path | Stages 2, 4 | No console-exporter step anywhere in Part 5. Grep: `ConsoleSpanExporter` absent from `tutorial/`. |
| P6 | No guidance on other OTel collectors | Stages 4, 6 | 5.5 shows the OTLP code variant (not run). 5.7 documents the env-var route and points to the adk.dev integrations list. Covered by documentation, not execution. |
| P7 | No sample output or explanation | Stages 2–7 | Each scenario has an **Expected output** block from a real run and a **What you are looking at** callout. |
| P8 | Interplay with logging plugins and native logging ignored | Stages 1, 2, 5, 7 | 5.2 shows the span knob before/after. 6.2/6.3 show which route sets the knob. 5.8 shows one turn in four places and states independent/correlated/duplicated per pair. |

## Research findings

### Q1. Can an ADK agent emit OTel telemetry from env vars alone?

Yes for CLI-launched agents (`adk web`, `adk api_server`, `adk deploy cloud_run`) and Agent Runtime. No for a plain script or hand-written server, which need one zero-argument call. P3 holds with that qualification.

Evidence:

- `maybe_set_otel_providers()` appends OTLP exporters when `OTEL_EXPORTER_OTLP_ENDPOINT` or a per-signal `_TRACES_`/`_METRICS_`/`_LOGS_ENDPOINT` var is set (`adk/telemetry/setup.py:45-56`, `:124-147`). Resource attributes come from `OTEL_SERVICE_NAME`/`OTEL_RESOURCE_ATTRIBUTES` (`setup.py:118-121`).
- The only caller inside ADK is the CLI server: `adk/cli/api_server.py:649-666`, `:668-677`, `:721-735`, wired at `:1173`. `runners.py` never sets a provider. `adk run` has no telemetry setup.
- Empirical: with `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` set, importing `InMemoryRunner` leaves a `ProxyTracerProvider`. Calling `_setup_telemetry(otel_to_cloud=False)` yields a real `TracerProvider` with an OTLP exporter.
- adk.dev traces, metrics, and logging pages describe the same export-then-`adk web` pattern.

Limits of the env-var path:

| Limit | Evidence |
|---|---|
| Needs `opentelemetry-exporter-otlp-proto-http`, not a base dependency. Already in the tutorial's `requirements.txt`. | `google_adk-2.8.0.dist-info/METADATA:32-33`, extras at `:97`, `:193`, `:249` |
| HTTP/protobuf only. No gRPC exporter imported. | `setup.py:150-167`; `OTEL_EXPORTER_OTLP_PROTOCOL=grpc` not found in ADK |
| Headers and timeout come from the OTel SDK's own env handling. | opentelemetry.io OTLP exporter config page |
| GenAI SDK auto-instrumentation only with `google-adk[otel-gcp]`; otherwise a startup WARNING. | `api_server.py:738-748` |
| Content knobs are separate vars: `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` (default `NO_CONTENT`), `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` (default true), `OTEL_SEMCONV_STABILITY_OPT_IN`, `ADK_TELEMETRY_SCHEMA_VERSION_OPT_IN`, `ADK_EXPERIMENTAL_TELEMETRY`. | `adk/telemetry/context.py:38-47`, `:85-118`; `_schema_version.py:40-91` |
| No CLI means one call: `maybe_set_otel_providers()` with no args honors the same vars. | `setup.py:45-74` |
| **`.env` cannot carry `OTEL_*` vars for `adk web`/`api_server`.** The agent's `.env` loads lazily on first agent load, after `_setup_telemetry` ran at server construction. Vars must be shell exports. | `agent_loader.py:331-332`, `api_server.py:1173`, `fast_api.py:314-318`, `envs.py:53-81` |
| **On your own server `.env` works, but a shell export still wins.** `bootstrap()` calls `load_dotenv`, which does not override a variable already in the environment. A leftover 5.2 export silently beats the 5.5 `.env` line; 5.5 Step 1 unsets it. | `examples/_common.py:49-55`; live run 2026-09-05 |
| **No env var selects the Google Cloud branch.** Only `--otel_to_cloud` does. `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` locally only adds a `User-Agent` header. A hand-supplied bearer token over generic OTLP would reach Google for traces only, with a one-hour token. Not run, not a tutorial path. | `api_server.py:649-666`; `_agent_engine.py:203-205`; `google_cloud.py:_get_gcp_span_exporter` |

### Q2. What does `adk web` do with the switch and env vars?

Flag: `--otel_to_cloud`. `--trace_to_cloud` is deprecated in its favor (`cli_tools_click.py`, `_deprecate_trace_to_cloud`).

Decision order in `_setup_telemetry` (`api_server.py:649-666`):

1. `--otel_to_cloud` → `_setup_gcp_telemetry` (`:680-718`). ADC credentials and project, `get_gcp_exporters(...)` for all three signals, resource from `get_gcp_resource(project_id)`. Traces and metrics go to `telemetry.googleapis.com/v1/{traces,metrics}` (`google_cloud.py:57-69`); logs via `CloudLoggingExporter` (`:264-281`, unguarded import, so `opentelemetry-exporter-gcp-logging` is required). Then the GenAI instrumentor if installed.
2. Else any `OTEL_EXPORTER_OTLP_*_ENDPOINT` set → `_setup_telemetry_from_env`.
3. Else a bare `TracerProvider` with only the dev UI's in-memory exporters.

Every branch installs the dev UI exporters (`api_server.py:458`, `:483`, `:1170-1178`), served at `/dev/apps/{app}/debug/trace/...` (`dev_server.py:796-804`). The switch and env vars only add export.

What ADK instruments on its own:

| Signal | Names | Source |
|---|---|---|
| Spans | `invocation` (root, schema v1), `invoke_agent {name}`, `call_llm`, `generate_content {model}`, `execute_tool {tool}`; also `send_data`, `execute_tool (merged)`, `compact_events …`, `handle_context_caching` | `_instrumentation.py:133,476,509`; `base_llm_flow.py:1732`, `:717`; `functions.py:526,774`; `tracing.py:1067,1121`; `compaction.py:60`; `google_llm.py:245` |
| Log events | `gen_ai.system.message`, `gen_ai.user.message`, `gen_ai.choice`; `gen_ai.client.inference.operation.details` under the experimental opt-in | `tracing.py` emit sites; `_stable_semconv.py:46-130`; `_experimental_semconv.py:619-636` |
| Metrics | `gen_ai.invoke_agent.duration`, `gen_ai.invoke_workflow.duration`, `gen_ai.execute_tool.duration`, `gen_ai.invoke_agent.inference_calls`, `gen_ai.invoke_agent.tool_calls`, `gen_ai.client.operation.duration`, `gen_ai.client.token.usage` | `_metrics.py:47-137` |

Not instrumented: inbound HTTP (the only middleware extracts `Google-Agent-Engine-Traceparent`, `fast_api.py:531-547`), Python `logging` (no `LoggingHandler` in ADK), httpx/gRPC clients (only under `GOOGLE_CLOUD_AGENT_ENGINE_ID` with extras, `api_server.py:749-767`), and Cloud Run's `X-Cloud-Trace-Context`.

### Q3. Same for `adk api_server`

Identical. Both commands share `fast_api_common_options` and build the server through `ApiServer.get_fast_api_app`, where `_setup_telemetry` runs (`api_server.py:1173`). `adk web` only adds the UI assets.

**Correction (2026-09-04 run).** The `/dev/.../debug/trace` endpoints are not available under `api_server`. Only `DevServer` registers them; the `web=False` path mounts none (`fast_api.py:265-285`). So with `api_server` and no export, in-memory spans are unreachable. `check_local.sh` uses `adk web`, and 5.3 reads spans back from Cloud after `--otel_to_cloud`.

Cloud Run via the CLI: `adk deploy cloud_run --otel_to_cloud` writes the flag into the container `CMD` (`cli_deploy.py:216`), so the same path runs under the service account's ADC, and `get_gcp_resource` merges `GoogleCloudResourceDetector` attributes.

### Q4. How does telemetry work in Agent Runtime?

**One switch.** `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` on the Reasoning Engine's `deployment_spec.env`. The `AdkApp` wrapper reads it at startup (`vertexai/adk.py:1767-1793`): `true`/`1` on, `false`/`0` off, anything else (including `unspecified`) None. With legacy `enable_tracing` at its default, the truth table (`:1795-1815`) reduces to tracing on only when the var is true. Logging follows telemetry (`:1767-1778`). No flag reaches the process; every tool below writes that env var.

| Way to set it | What it writes | Evidence |
|---|---|---|
| `adk deploy agent_engine --otel_to_cloud` | `…ENABLE_TELEMETRY=true` **and** `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (unless `.env` sets it) | `cli_deploy.py:1273-1282`, `:1293-1300`, `:1305-1430` |
| `adk deploy agent_engine`, var in the agent's `.env` | Same var only; CLI prints that `.env` set it | `cli_deploy.py:1283-1291` |
| `--agent_engine_config_file` (`.agent_engine_config.json` with an `env_vars` object) | Only when `.env` is absent or empty. If `dotenv_values(.env)` yields anything, `agent_config['env_vars'] = env_vars` replaces the file's `env_vars` wholesale (plain assignment, no merge) and the CLI prints `Overriding env_vars in agent platform config`. So "base config in `.env`, knobs in the config file" cannot work. Not used by the tutorial. | `cli_deploy.py:1154-1159`, `:1226-1234`, `:1293-1303` |
| `agents-cli deploy` (target `agent_runtime`, v1.1.0) | `setdefault` of the var to `true`, plus `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`. Scaffolded app calls `setup_agent_engine_telemetry()` itself and passes `otel_to_cloud=False` to ADK. | `google/agents/cli/deploy/agent_runtime.py:137-138`; scaffold `service.tf:57-64`; `app_utils/telemetry.py:28-33`, `:87-104` |
| `vertexai` SDK `create`/`update` | Whatever you pass. Omit the var and the SDK injects `unspecified`, "in order to achieve default-on telemetry". | `vertexai/_genai/agent_engines.py:2355`, `:2398`; `_agent_engines_utils.py:2156-2185` |
| Cloud Console toggle | Presumably the same var, server-side. ASSUMPTION; known only from deprecation text at `vertexai/adk.py:1005-1027`. | |
| Legacy `AdkApp(enable_tracing=True)` | Overrides the env var. Deprecated; the warning says it breaks the Console toggle. | `vertexai/adk.py:1005-1027`, `:1795-1815` |

**`unspecified` is the crux.** The wrapper reads it as None (off). The SDK docstring implies default-on, which only works if the platform resolves it server-side. Local code does not say which. `adk deploy agent_engine` never produces `unspecified`, so a control deploy must omit the flag and the `.env` line.

Docs: the Agent Runtime tracing page says set the var to `"true"`, optionally `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY`, and enable the Telemetry API. The logging page gives resource `aiplatform.googleapis.com/ReasoningEngine` and log ids `reasoning_engine_stdout`/`_stderr`. ASSUMPTION: the server-side class is the `vertexai` `AdkApp` template read here.

`OTEL_EXPORTER_OTLP_*` on Agent Runtime does nothing: the native wrapper never calls `maybe_set_otel_providers`. ASSUMPTION, consistent with Q1.

What ADK changes under `GOOGLE_CLOUD_AGENT_ENGINE_ID`: schema v2 (root span `invoke_workflow {root}`, `_schema_version.py:40-91`); resource gains `cloud.platform=gcp.agent_engine`, `service.name=<engine id>`, `cloud.resource_id`; logs exporter writes JSON to stdout under log name `adk-on-agent-engine`; metrics use a request-driven reader; trace context comes from `Google-Agent-Engine-Traceparent`.

**Contradicted tutorial claim.** `06-agent-runtime.md:16-18` and `deploy_agent_engine.sh:73-74` said traces appear automatically and the flag only adds logs and metrics. The truth table says default-off, and the tutorial's deploys always passed the flag. Stage 1 marks it unverified; Stage 5 tests it.

BYOC: `agent_runtime_byoc/main.py:56` builds its own `AdkApp`, so the same var governs it if the deploy passes it. `deploy_byoc.py:48-53` does not today. Out of scope beyond one sentence.

### Q5. OTel spans vs. logging plugins vs. ADK-native logging

| Pair | Relationship | Evidence |
|---|---|---|
| Python `logging` (streams 1–3) ↔ OTel | **Independent.** No bridge; CLI log format carries no trace id. | No `LoggingHandler` in ADK; `cli/utils/logs.py:25-27` |
| `LoggingPlugin`/`DebugLoggingPlugin` ↔ OTel | **Independent.** Neither imports OpenTelemetry. They run inside the spans but do not read them. | `plugins/logging_plugin.py` (`:293` print); contrast `bigquery_agent_analytics_plugin.py:825-860`, which inherits `trace_id` |
| OTel `gen_ai.*` events ↔ spans | **Correlated automatically.** The OTel API stamps trace/span ids on every LogRecord; the Cloud Logging exporter writes them as `logging.googleapis.com/trace` and `spanId`, and names the log after the event. | `otel-sdk/_logs/_internal/__init__.py:107-115`; `gcp-logging/.../__init__.py:324-331`, `:364-367`, `:417-421` |
| Part 4's `X-Cloud-Trace-Context` trace ↔ OTel trace | **Different ids.** ADK never extracts Cloud Run's header. | `fast_api.py:531-547` |

Duplication: with defaults one prompt can appear in four places: `google_adk` DEBUG lines, `LoggingPlugin` output, the span attribute `gcp.vertex.agent.llm_request` (on by default, `context.py:108-113`, `tracing.py:629-635`), and `gen_ai.*` events when capture is on. Join key: the plugin's `Invocation ID` = `gcp.vertex.agent.invocation_id` on spans (`tracing.py:622,744`); `gen_ai.conversation.id` = session id (`:229,778`).

Two more contradicted claims, both fixed in Stage 1:

- `05-otel.md:76-83` said only a custom span processor strips `llm_request`/`llm_response`. `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` does it, and `adk deploy agent_engine --otel_to_cloud` sets it for you.
- `05-otel.md:70-71` and `08_otel_cloud.py:35` said the content knob must be set before ADK is imported. In 2.8.0 both knobs are read when an invocation builds its `TelemetryConfig` (`tracing.py:865-873`, `context.py:93-113`, `:179-180`), so they can live in `.env`, unlike the exporter endpoint vars.

Not found: any ADK doc on how OTel log records relate to Python logging.

## Scope

**In scope**

| File | Role |
|---|---|
| `tutorial/part-5/` (`index.md`, 5.0–5.8) | Rewritten top to bottom (Stages 2–4, 6, 7). |
| `tutorial/part-6/` (`index.md`, 6.1–6.4) | Telemetry paragraphs rewritten (Stages 1, 5). |
| `tutorial/how-to-choose.md` | Decision rows, "Beyond logging", verification status, references (Stages 1, 5, 6, 8). |
| `TUTORIAL.md` | Part 5 contents row; stream-4 "lands in" label (Stage 8). |
| `README.md` | Files table rows for example 08 and `otel/` (Stage 8). |
| `examples/08_otel_server.py` | Renamed from `08_otel_cloud.py`, rewritten as a minimal FastAPI server. Only telemetry lines: `get_gcp_exporters(enable_cloud_logging=True)` + `maybe_set_otel_providers([hooks])`. |
| `deploy/Dockerfile.otel_server` (new) | Container for example 08, following the `deploy/Dockerfile` pattern. No `.env` baked in. |
| `deploy/deploy_agent_engine.sh` | Comment block corrected (Stage 1); `ENABLE_VIA_ENV` branch and venv fix (Stage 5). Since 2026-09-05 used only by 1.6; 6.2/6.3 run inline commands. Its header still describes the 6.2/6.3 routes (stale, not edited). |
| `deploy/env/` (new, 2026-09-05) | Canned `demo_agent/.env` contents for Part 6: `default.env` and `6.2a.env` (identical: `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, `GOOGLE_CLOUD_LOCATION=global`, `LOG_LEVEL=info`), `6.2b.env` (adds the switch and both content knobs). No `GOOGLE_CLOUD_PROJECT`. Unignored via a negation in the repo `.gitignore`. |
| `requirements.txt` | `google-adk[otel-gcp]>=2.8.0`, `opentelemetry-exporter-otlp-proto-http`, `opentelemetry-exporter-gcp-logging`. Done. |
| `demo_agent/requirements.txt` | Container deps for `adk deploy cloud_run --otel_to_cloud`, including `[otel-gcp]`. Done. |
| `otel/check_local.sh` (new) | The one automated check: plain `adk web`, assert span names via the debug endpoint. |
| `CLAUDE.md` | Only if a new convention is needed. |

**Out of scope.** The ADK and vertexai SDKs. Parts 1–4 except cross-references. The four-streams framing. `agent_runtime_byoc/` beyond one sentence. The Part 4 custom server's Cloud Run deploy. Running any non-Google backend. Modifying `06_custom_server.py`. Any docs-site build (none exists).

## Target shape

**Part 5**

| § | Content |
|---|---|
| 5.0 | What stream 4 is, one diagram (agent → in-process exporters, or → telemetry.googleapis.com / Cloud Logging). The five span names. |
| 5.1 | Nothing configured: `adk web` already traces. The Trace tab in the UI. In memory, per process, gone on restart. |
| 5.2 | `adk web --otel_to_cloud` locally. Required shell exports (`OTEL_RESOURCE_ATTRIBUTES` for the metrics 400, `OTEL_SEMCONV_STABILITY_OPT_IN`), why they must be exports. One UI turn, `gen_ai.*` in Logs Explorer with `<elided>`, then the event knob turns content on. As shipped, also one Trace Explorer check: the span knob (`ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`) empties `llm_request` while logs keep content. Two independent knobs, live. |
| 5.3 | `adk api_server --otel_to_cloud` locally, same exports with `NO_CONTENT`, curl-driven, read through Logs Explorer. |
| 5.4 | `adk deploy cloud_run --otel_to_cloud`, inline commands. Deploy, curl, read `gen_ai.*` in Logs Explorer, teardown. Two traps in one aside. `.env` ships in the image; `GOOGLE_CLOUD_LOCATION` repeated in `--set-env-vars` to beat the Dockerfile `ENV`. |
| 5.5 | Your own server: `08_otel_server.py` installs the Cloud Logging exporter with two calls. Unset any shell copy of the content knob, run locally, curl, read `gen_ai.*`; root-`.env` knob before/after (all `OTEL_*` vars work in `.env` here because the server loads it first), Step 3 also opting into the experimental convention, each change followed by restart + curl + re-query. Deploy with `gcloud run deploy --source`, knob and opt-in via `--set-env-vars`. A second, non-runnable OTLP snippet. |
| 5.6 | The two content knobs as reference: spans vs events, turning content on deliberately, `RunConfig` scoping. |
| 5.7 | Other backends, reference only: OTLP env vars for CLI-launched servers, vendor headers, http/protobuf only, the adk.dev integrations list. Nothing run. |
| 5.8 | Relation to Parts 1–4: one turn, four places; independent / correlated / duplicated. |

**Part 6 (telemetry subsections)**

| § | Content |
|---|---|
| 6.1 | One switch, two ways to set it. The flag also sets the span knob to false; `.env` does not. Setting neither means the platform decides; do not rely on it. One BYOC sentence. |
| 6.2 | Deploy A, the flag. `cp deploy/env/6.2a.env demo_agent/.env`, inline `adk deploy agent_engine --otel_to_cloud`, grep the engine id, read the env list (the two vars the CLI added), query, `sleep 15`, read the logs, restore `default.env`. Deep dive: why the copy and restore. |
| 6.3 | Deploy B, `.env`: `cp deploy/env/6.2b.env demo_agent/.env`, same deploy with no flag, `$ENGINE_ID_ENV`. Same env-list read (the three `.env` lines, nothing added), query, logs, restore. On this route you set the span knob yourself. |
| 6.4 | What the platform changes, limited to what 6.2/6.3 showed. |

Diagram budget (Mermaid): 5.0 flow and 5.8 four-places picture. Nothing else.

## Stages

Each stage leaves the docs coherent if work stops after it. M = mechanical, J = judgment.

### Stage 1 · Correct three wrong claims in place (J; done)

Files: `05-otel.md:68-83`, `06-agent-runtime.md:12-18`, `deploy_agent_engine.sh:73-74`, `08_otel_cloud.py:35,53-54`, `07-how-to-choose.md`.

- [x] Replace the 05 WARNING: `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` strips the vendor attributes; the agent_engine deploy flag sets it; a span processor is the fallback for other attributes. Cites `context.py:107-113`, `tracing.py:629-635`, `cli_deploy.py:1281-1282`.
- [x] Drop "must be set before ADK is imported" from 05 and example 08. Grep confirmed no import-time cache (`context.py:42-46,94-110`, `_stable_semconv.py:46`, `tracing.py:90,100,148`).
- [x] Rewrite the 06 bullet: the env var governs telemetry; the flag or a `.env` line sets it; set it explicitly.
- [x] Same correction in the script heredoc.
- [x] Mark the "automatic traces" claim unverified in 07.

Verify: `grep -n "automatically"` on the two files has no telemetry hit. Pass.

### Stage 2 · 5.0 opening, 5.1 zero-config, 5.2 `adk web --otel_to_cloud` (J; done, runs verified)

Goal: the reader sees `adk web` trace with nothing configured, adds one flag, and finds the same run in Cloud without code.

5.1: plain `adk web`, one turn, the Trace tab in the UI (not curl). Three facts: a real provider is always installed (`api_server.py:649-666`), the exporters write to process memory (`:458-518`), nothing leaves the process.

5.2 flow:

1. Export two shell vars before starting. `OTEL_RESOURCE_ATTRIBUTES="service.instance.id=laptop-1,cloud.region=us-central1"` avoids the metrics 400 (laptop-only; Cloud Run and Agent Runtime supply these). `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental` matches the Agent Runtime docs.
2. Start `adk web --otel_to_cloud ./`, one London turn in the UI.
3. Read `gen_ai.*` in Logs Explorer: content `<elided>` because capture defaults to `NO_CONTENT` (`context.py:93-105`). Note the aligned `trace`/`spanId`.
4. Stop, `export OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=EVENT_ONLY`, restart, new session, repeat. Content now present. Rule: keep content off in production unless reviewed.
5. As shipped: check Trace Explorer, then set `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` and restart. The span's `llm_request` goes `{}` while logs keep content.

Stated once here: why vars must be shell exports (`api_server.py:1173` runs before `agent_loader.py:331-332`); prerequisites (ADC, project, Telemetry API, `roles/telemetry.writer` or the three granular roles, the two exporter packages); the startup WARNING and what `[otel-gcp]` adds. ASSUMPTION: the extra does not double `generate_content` spans. NEEDS-RUN (open question 5).

### Stage 3a · 5.3 `adk api_server --otel_to_cloud` (M; done, runs verified)

Export the same two vars plus `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`. Reuse 1.3's curl block, read `gen_ai.*` in Logs Explorer. One sentence on the shared code path (`fast_api_common_options`, `api_server.py:1173`). `<elided>` confirms `NO_CONTENT`.

### Stage 3b · 5.4 `adk deploy cloud_run --otel_to_cloud` (J; done, deploy verified)

Four inline steps: deploy `./demo_agent`, curl the service (URL via `gcloud run services describe`), read `gen_ai.*` in Logs Explorer, teardown. Events land on a `generic_task` resource whose `job` is the service name. `GOOGLE_CLOUD_LOCATION=global` repeated in `--set-env-vars` to beat the Dockerfile `ENV` (`cli_deploy.py:193`). Two traps in one aside. Cut: Cloud Trace read-back, `CMD` demo, `--log_level` trap, wrapper-script machinery.

### Stage 4 · 5.5 your own server, 5.6 content knobs (J; done)

Goal: make explicit the one case that needs code, and which knob controls prompt text where.

5.5 (redesigned 2026-09-05; the design notes now live in the Build decisions row): a stripped `06_custom_server.py` with `App` + `Runner` in a `lifespan`, `/chat`, `uvicorn.run`, plus the two telemetry calls. Logging-only, no `get_gcp_resource`. Flow as shipped: Step 1 unsets any shell export of the content knob (it would shadow `.env`), runs locally, curls; Step 2 reads `gen_ai.*` on `generic_task` with `job` = `OTEL_SERVICE_NAME`; Step 3 edits the **root** `.env` once (`true` commented out, `NO_CONTENT` plus the experimental opt-in), restarts, re-curls, re-queries; Step 4 deploys with `gcloud run deploy --source`, knob and opt-in via `--set-env-vars`. Teaching point: `.env` works here because `bootstrap()` loads it before the exporters are built. Second snippet, not run: `maybe_set_otel_providers()` with `OTEL_EXPORTER_OTLP_ENDPOINT`/`_HEADERS` set (`setup.py:45-74`, `:124-147`).

5.6, reference only: the two-knob table (defaults, safe values), turning content on (`EVENT_ONLY`/`SPAN_ONLY`/`SPAN_AND_EVENT`, `context.py:93-105`), `RunConfig.telemetry` scoping (`run_config.py:249-255`), and that the agent_engine deploy flag flips the span knob (`cli_deploy.py:1281-1282`).

Verify: local run verified live 2026-09-05 (server starts, `/chat` answers, `gen_ai.*` on `generic_task` with `job` = `OTEL_SERVICE_NAME`, knob both ways under the stable convention). `py_compile` passes. Step 3 under the experimental convention NEEDS-RUN (the page still says every entry "reads `<elided>`", which is stable-convention wording). Cloud Run deploy NEEDS-RUN; Step 4 carries no fabricated output.

### Stage 5 · 6.1–6.4 Agent Runtime (J; done, two live deploys)

Files: `06-agent-runtime.md`, `deploy_agent_engine.sh` (`ENABLE_VIA_ENV` branch; also fixed to call `./.venv/bin/adk`, since PATH resolved to the 2.5.0 sibling), `07-how-to-choose.md`.

As built:

- 6.1 written from citations: the switch (`vertexai/adk.py:1767-1815`), the two routes (`cli_deploy.py:1273-1282`, `:1283-1291`), the `unspecified` note, a BYOC sentence.
- 6.2 (flag) and 6.3 (`.env` route) both deployed. The read-back that worked is the env list via the `vertexai` SDK: `engine.api_resource.spec.deployment_spec.env`. **`gcloud ai reasoning-engines` does not exist** in this install. 6.2's list shows the two CLI-added vars; 6.3's shows the three `.env` lines and nothing else. Real captures.
- **Verified negative.** Querying a telemetry-enabled engine produced no `gen_ai.*` logs and no Cloud Trace spans, only `reasoning_engine_stderr` INFO lines. Two control deploys, multiple queries, 40 minutes. Part 6 states only what surfaced; the destination question is open in How to choose.
- 6.4: observed differences only, including the "did not surface" row.

Cloud hygiene: both control engines and one stray deleted; Jeff's pre-existing engines untouched; `demo_agent/.env` restored by the script trap.

**Reworked 2026-09-05 (overrides the above where they differ).** The script left 6.2/6.3. Each page now: copies a canned env file from `deploy/env/`, runs `adk deploy agent_engine` inline (with or without the flag), greps `reasoningEngines/[0-9]+` from the captured output, reads the env list via the SDK with project, region, and id passed as argv, sends one `stream_query`, sleeps 15 s, runs `gcloud logging read`, then `cp deploy/env/default.env demo_agent/.env`. 6.3 is self-contained. 6.2 re-run live end to end; verified negative reconfirmed (617 entries, none `gen_ai.*`). The reader restores `demo_agent/.env`; there is no trap. Details in the 2026-09-05 session log.

### Stage 6 · 5.7 other backends, reference only (J; done)

For CLI-launched servers, env vars replace the flag when `--otel_to_cloud` is absent (`api_server.py:657-658`, `setup.py:124-147`). Four-row var table with opentelemetry.io defaults. Shell exports, not `.env`, for CLI servers; `.env` works on your own server (5.5 contrast). http/protobuf only. Point to the 5.5 snippet, the adk.dev integrations list, and MLflow as the code-path example (`http://localhost:5000/v1/traces`, `x-mlflow-experiment-id`). Every block labeled "not run here". Nothing runs in this stage.

### Stage 7 · 5.8 logging interplay (J; done, verified live)

The four places: `google_adk` DEBUG lines, `LoggingPlugin` output, the span attribute `gcp.vertex.agent.llm_request`, the `gen_ai.*` events. Read-back: Logs Explorer (`logName=~"gen_ai\."`) for the OTel half, terminal stdout for the rest. The span attribute is cited as a table row, not a Trace Explorer step. Content is the Q5 table and the join key. Runnable: a turn against the 5.5 server with `LoggingPlugin` and DEBUG.

### Stage 8 · Cross-references, tables, link check (M; done)

Line numbers stale; grep for text. Fixes made:

- `TUTORIAL.md` Part 5 row reworded toward "GenAI `gen_ai.*` events to Cloud Logging (traces/metrics also flow), and the content-capture privacy knob". Stream-4 label → "Cloud Logging (`gen_ai.*`), plus Cloud Trace / Monitoring, or any OTLP collector".
- `README.md` example-08 row updated.
- `07-how-to-choose.md`: decision rows, verification status, references (adk.dev observability pages, Agent Runtime tracing page, OTel OTLP env-var page).
- No stray `08_otel_cloud` or `deploy_otel_cloudrun.sh` references.

Verify: `grep -rn -E "05-otel|Part 5|08_otel|08_otel_cloud|deploy_otel_cloudrun|Cloud Trace" ai/adk/logging` shows only intended hits; link check passes.

## Verification

**Common harness.** Fresh `python3.13 -m venv .venv && pip install -r requirements.txt`, `.env` from `.env.example`, `source env.sh`, Docker running. Prompt for all runs: "What's the weather in London?". Expected spans (schema v1): `invocation`, `invoke_agent weather_agent`, `call_llm` ×2, `generate_content gemini-3.7-flash` ×2, `execute_tool get_weather`. Expected events per LLM call: 1× `gen_ai.system.message`, ≥1× `gen_ai.user.message`, 1× `gen_ai.choice` (verified 2026-09-05: 1 + 1 + 1 on the first call, 1 + 3 + 1 on the second, eight total). Link check: `lychee --offline 'ai/adk/logging/**/*.md'` or equivalent.

| Stage | Runs | Pass condition | Status |
|---|---|---|---|
| 1 | none | grep clean; claim marked unverified | Pass |
| 2 | plain `adk web`; `--otel_to_cloud` with event knob then span knob | 5.1: seven spans in the Trace tab. 5.2: `gen_ai.*` in Logs Explorer `<elided>`, then with content; Trace Explorer shows `llm_request` full, then `{}` | Pass; `check_local.sh` covers 5.1 |
| 3 | `api_server --otel_to_cloud` + curl; `adk deploy cloud_run` + curl + teardown | 5.3: events `<elided>`. 5.4: service Ready, `/run` answers, events on `generic_task` | Pass |
| 4 | example 08 locally + knob; Cloud Run deploy | Local: server starts, `/chat` answers, events on `generic_task`, knob both ways. Cloud Run: Ready, `/chat` works, content absent from `--set-env-vars` | Local pass (stable convention); Step 3 experimental NEEDS-RUN; Cloud Run NEEDS-RUN; `py_compile` passes |
| 5 | 6.2 (`6.2a.env` + flag) and 6.3 (`6.2b.env`, no flag) inline deploys; one query each; delete both | Env lists read via SDK match the two routes. No `gen_ai.*` or spans surfaced. | Pass with verified negative; 6.2 reconfirmed 2026-09-05 with the inline commands |
| 6 | none | var table matches `setup.py:124-147`; every block labeled "not run here" | Pass; link check |
| 7 | DEBUG + `LoggingPlugin` + OTel export, one turn | same `Invocation ID` in plugin output and spans; same prompt string in all places; events `<elided>` | Pass |
| 8 | none | links resolve; cross-ref grep clean | Pass |

## Open questions

**Decisions (Jeff, 2026-09-04)**

1. Third Agent Runtime deploy to record the default: skip. 6.1 says the platform decides and claims no default.
2. BYOC telemetry: out. One pointer sentence in 6.1.
3. `adk deploy cloud_run` traps: moved into 5.4.

**Facts the runs supplied**

4. **Which exporter set runs on native Agent Runtime?** Partially resolved. Both routes set the env vars correctly, but no `gen_ai.*` logs, no `adk-on-agent-engine` log, and no spans appeared over 40 minutes. Sub-questions about log name, root span, and metrics are moot until the destination is known. It may need Console-side enablement or a path the SDK deploy does not trigger. Reconfirmed 2026-09-05 on a flag-route engine deployed with the inline 6.2 commands: 617 entries, all `reasoning_engine_stdout`/`_stderr`. Open.
5. **Does `[otel-gcp]` double `generate_content` spans?** Not verified. Without the extra, plain `adk web` produced one `generate_content` per `call_llm`. NEEDS-RUN.
6. Resolved details:
   - **Env-list field path.** `client.agent_engines.get(name=…).api_resource.spec.deployment_spec.env`, a list of `EnvVar(name, value)`.
   - **Cloud Run resource on `gen_ai.*` entries.** `generic_task` with `resource.labels.job` = `OTEL_SERVICE_NAME`. Filter on `job` or `logName=~"gen_ai\."`.
   - **Metrics resource.** `prometheus_target`; series appear as `prometheus.googleapis.com/gen_ai.*` (name not confirmed against a real run). Locally needs `service.instance.id` and a real `cloud.region` via `OTEL_RESOURCE_ATTRIBUTES`. Spans and logs need none of this.
   - **IAM.** `roles/telemetry.writer` bundles traces, metrics, and logs. Granular: `cloudtrace.agent`, `monitoring.metricWriter`, `logging.logWriter`. Not exercised as a minimal set (ADC identity was owner).

**Resolved**

7. Third-party target: dropped. MLflow is the cheapest candidate if that changes.
8. Example 08 filename: `08_otel_server.py`.
9. Where `OTEL_*` vars live: `env.sh`. `adk web` loads `.env` after telemetry setup (`agent_loader.py:331-332`, `api_server.py:1173`). Stated in 5.7 with citation.
10. Part 6 deploy mechanism: inline commands plus `deploy/env/{default,6.2a,6.2b}.env`, not the wrapper script and not `.agent_engine_config.json` (Q4 merge rule). Decided 2026-09-05.
11. Which `.env` 5.5 edits: the root `ai/adk/logging/.env`. Named explicitly on the page.
