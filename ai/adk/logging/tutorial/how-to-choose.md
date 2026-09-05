[← 6.4 · What the platform changes](part-6/6.4-platform-changes.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# How to choose & reference

*The decision table, best-practice summary, verification status, and links.*

---

## How to choose

| You are... | Use | Why |
|---|---|---|
| Getting the shape of a run | `--log_level INFO` | Lifecycle without contents. |
| Debugging what the model saw | `--log_level DEBUG` | Full prompt, history, tool schema. |
| Reading tool calls live in dev | `LoggingPlugin` (3.1, 3.5) | Clean narration + tokens. Prints, so dev only. |
| Capturing one bad turn in full | `DebugLoggingPlugin` (3.3, 3.5) | Complete YAML record, secrets redacted. |
| Emitting metrics for production | Custom `BasePlugin` (4.1) | Real `logging` records; queryable, alertable. |
| Logging or guarding one agent only | Per-agent callback (4.4) | Siloed by design; can short-circuit a step. |
| Running your own HTTP server | `dictConfig` + the 4.1 plugin (4.2) | Own all four streams in one place. |
| Seeing raw logs reach the cloud, fast | Cloud Run Job/service, no JSON (1.4, 1.5) | Zero setup; but severity is Cloud Run's guess (Default), not yours. |
| Deploying to Cloud Run for real | JSON to stdout + trace field (4.3) | Auto-ingested; severity you set; grouped by request. |
| Deploying the agent to Agent Runtime | `adk deploy agent_engine` (1.6) + `--otel_to_cloud` | Managed; but the platform owns log format/stream. |
| Keeping your own logging on Agent Runtime | Custom container / BYOC (1.6) | Your server, your format; you implement the runtime contract. |
| Finding where latency goes | `--otel_to_cloud` / `get_gcp_exporters` | Timed span tree in Cloud Trace. |

Best-practice summary:

- Serve at **INFO or WARNING** in production; keep DEBUG for active debugging.
- Emit **one JSON object per line** with an explicit **`severity`**, and log to
  **stdout**. Do not rely on Cloud Run inferring severity from the stream: 1.4
  and 1.5 showed plain stderr lines landing as Default, and the common rule says
  ERROR, so set severity yourself.
- Correlate with the **trace** field so a request is one filterable group.
- Keep GenAI content capture at **`NO_CONTENT`** unless you have a reviewed reason.
- Tune the framework as a group via `logging.getLogger("google_adk")`, and
  silence `uvicorn.access` health-check spam.
- Remember which stream a flag configures. Most confusion is a flag aimed at the
  wrong stream.

---

## Beyond logging

This tutorial stopped at logging and the log-facing side of tracing. The wider
observability story, briefly:

- **Cloud Trace** spans (Part 5) are worth exploring on their own for latency
  breakdowns across `call_llm` and `execute_tool`.
- **BigQuery Agent Analytics** (`BigQueryAgentAnalyticsPlugin`) logs structured
  agent events to BigQuery for conversational analytics and LLM-as-judge evals.
- **Third-party platforms** (AgentOps, Phoenix, MLflow, Weave, and others)
  integrate over OpenTelemetry for session replays and dashboards.

The ADK observability skill and `https://adk.dev/observability/` cover these.

---

## Verification status

Verified by running end to end against a real project (`jwd-gcp-demos`, Vertex
AI, Gemini 3.7 Flash):

- Examples 01 through 09 all run; every console block above is captured from a
  real run. The Part 4 custom server (`06_custom_server.py`) was run locally
  (2026-09-04): every stream (your code, the plugin, the tool, and `google_adk`)
  emits JSON with an explicit `severity` and, when the `X-Cloud-Trace-Context`
  header is present, the same `logging.googleapis.com/trace` value.
- Part 1's DEBUG/INFO/WARNING differences, Part 3's plugin narration, and Part 4's
  JSON events, custom server, and trace correlation are all reproduced as shown.
- Example 08 `cloud` mode exports to Cloud Trace and Cloud Logging without error
  via application-default credentials.
- The **cloud deploys in 1.4-1.6 were all run** against `jwd-gcp-demos`
  (2026-09-03) and every console block in those sections is captured from the
  real run: the Cloud Run Job (1.4), the Cloud Run service (1.5), the native
  Agent Runtime agent and BYOC container (1.6). The findings that differ from
  common advice, stderr landing as Default not ERROR (1.4/1.5), the platform
  owning log format on native Agent Runtime (1.6), the project-level
  `artifactregistry.reader` and reserved-var model-region traps (1.6 BYOC), are
  all from those runs.
- The **plugin Cloud Run Jobs in 3.2, 3.4, and 4 were run** against `jwd-gcp-demos`
  (2026-09-03) with [deploy/deploy_plugin_job.sh](../deploy/deploy_plugin_job.sh).
  3.2's two findings (the narration survives `LOG_LEVEL=WARNING` untouched; it
  lands on stdout with Default severity and literal ANSI bytes) and 3.4's (the
  YAML is discarded with the container until a Cloud Storage volume is mounted,
  and the plugin then emits its mode-600 warning against the FUSE mount) are both
  from those runs. Part 4's Job confirmed the structured payoff: the plugin's JSON
  parsed into queryable `jsonPayload` fields (`event`, `tool`, `latency_ms`,
  `status`) and its `severity` landed as `INFO`, not Default.

- **5.5's minimal OTel server was run locally** against `jwd-gcp-demos`
  (2026-09-05) with [examples/08_otel_server.py](../examples/08_otel_server.py):
  the server starts, `/chat` returns a weather answer, and the `gen_ai.*` events
  land in Cloud Logging on a `generic_task` resource whose `resource.labels.job`
  is the `OTEL_SERVICE_NAME` (`weather-agent`). Content knob verified live via
  `.env`: `...CAPTURE_MESSAGE_CONTENT=true` → the prompt text rides in the
  entry; `NO_CONTENT` → every entry's `content` is `<elided>`. Logging-only
  export needs **no** `get_gcp_resource` (that was a spans/`telemetry.googleapis.com`
  concern); the Cloud Logging exporter takes the project from ADC. **5.5's Cloud
  Run deploy is NEEDS-RUN** — the inline `gcloud run deploy --source` path and
  `deploy/Dockerfile.otel_server` are written but not yet deployed.
- **Part 5's local and Cloud Run runs (sections 5.0-5.4) were executed** against
  `jwd-gcp-demos` (2026-09-04); every block in those sections is from them.
  - 5.1: plain `adk web` traces one turn into process memory with nothing
    configured; the seven expected spans were read back from the dev server's
    `/dev/apps/demo_agent/debug/trace/session/{id}` (the endpoint the **Trace tab**
    reads, which the rewritten 5.1 now points readers to instead of curl).
    `adk api_server` installs the same exporters but serves no `/dev` route
    (confirmed `404`), so [otel/check_local.sh](../otel/check_local.sh) uses
    `adk web`.
  - 5.2: `adk web --otel_to_cloud` exported the same turn to Cloud Trace, Cloud
    Logging (`gen_ai.*`) and Cloud Monitoring. Findings: OTLP metrics land as
    `prometheus.googleapis.com/gen_ai.*` on the `prometheus_target` resource and
    need `OTEL_RESOURCE_ATTRIBUTES` (a `service.instance.id` and a real
    `cloud.region`) locally or every batch returns `400`; `google-adk[otel-gcp]`
    does not duplicate the `generate_content` span. **Restructured, verify by
    console:** the rewritten 5.2 is five steps read back in the Cloud console (Logs
    Explorer, Trace Explorer), no `gcloud logging read` blocks. Step 1 runs under
    **stable** semconv (`NO_CONTENT`): eight split `gen_ai.system.message` /
    `user.message` / `choice` logs for the turn, content elided in `jsonPayload`,
    on `generic_node` — the shown `gen_ai.choice` JSON is a real capture (trace
    `c5fdba98…`, 2026-09-05). Step 2 sets
    `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true`: the same eight logs
    now carry the messages in `jsonPayload.content` — real capture (system message
    and final `gen_ai.choice`, trace `9d24673b…`, 2026-09-05) — then checks whether
    the content also lands on the `call_llm` **span** attributes. Step 3 sets
    `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` to turn span content off while the
    log content stays. Step 4 adds the **experimental** opt-in
    (`OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`) with `NO_CONTENT`:
    one consolidated `gen_ai.client.inference.operation.details` entry per model
    call, metadata in `labels`, no `jsonPayload`, on `generic_node` — the shown JSON
    entry is a real capture (trace `3b80ad2b…`, 2026-09-05). Step 5 sets `EVENT_ONLY`
    on that same shape: the two consolidated entries now carry
    `gen_ai.system_instructions` / `input.messages` / `output.messages` in `labels`
    (no `jsonPayload`, unlike stable) — real capture (trace `acacdad7…`, 2026-09-05).
    Verify-by-console beat still open: the Step 2/3 span attributes in Trace Explorer
    (whether `=true` reaches `gcp.vertex.agent.llm_request` / `llm_response`, and
    whether `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` empties them), not captured.
  - 5.3: `adk api_server --otel_to_cloud` produced the same tree (trace
    `fb802902…`) in the original run. The rewritten 5.3 is logs-only (three shell
    exports, curl in, Cloud Logging out; content `NO_CONTENT`) and its output
    blocks are `TODO(verify)` placeholders pending a fresh run — the Cloud Run
    deploy that the earlier 5.3 folded in now lives entirely in 5.4.
  - 5.4: `adk deploy cloud_run --otel_to_cloud ./demo_agent` deployed the agent
    with the flag; one turn read back with `gen_ai.*` logs on a `generic_task`
    resource (job = service name), content `<elided>` proving `demo_agent/.env`'s
    `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` shipped in the image. On Cloud
    Run the metrics export needs no `OTEL_RESOURCE_ATTRIBUTES`. A bare-`google-adk`
    container boot-crashes at the OTLP exporter import, which the agent-folder
    `requirements.txt` prevents. 5.4 is now inline copy-paste commands (the
    `deploy_otel_cloudrun.sh` wrapper was dropped). The service was deleted after
    the run.
  - Re-run checklist: `gcloud auth application-default login`; enable
    `telemetry.googleapis.com`; `export OTEL_RESOURCE_ATTRIBUTES=…` for a local
    `--otel_to_cloud` run; keep the `.env` knob line; prompt
    "What's the weather in London?".

Not verified here (documented, run them yourself):

- **5.2's span-content check (Steps 2-3, Trace Explorer).** One thing in the
  restructured 5.2 is described from the source but not stored as a capture: the
  **span** attributes — whether `=true` (Step 2) also puts the prompt/reply on the
  `call_llm` span's `gcp.vertex.agent.llm_request` / `llm_response`, and whether
  `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` (Step 3) empties them while the logs
  keep content. Every log-side block in 5.2 is a real capture: Steps 1, 2, 4, and 5
  (traces `c5fdba98…`, `9d24673b…`, `3b80ad2b…`, `acacdad7…`).
- **The rewritten 5.3 local run.** Re-run `adk api_server --otel_to_cloud` with the
  three shell exports (`OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental`,
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT`), curl the London
  turn, read `gen_ai.*` back from Cloud Logging. Both output blocks in 5.3 are
  `TODO(verify)` (response text; the eight-row `<elided>` logging table with real
  trace/span ids). The original 5.3 run above (trace `fb802902…`) predates the
  three-export rewrite.
- The `deploy/deploy_cloudrun.sh` deploy of the Part 4 custom server end to end.
  The formatter and trace correlation are verified locally (4.2); the
  containerized Cloud Run deploy of it (4.3) is not.
- Whether an Agent Runtime deploy **without** `--otel_to_cloud` and without
  `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY` in `.env` produces traces. An
  earlier version of Part 6 said traces appear automatically; every deploy run
  here passed the flag or set the var, so that case was never exercised. Part 6
  now says "the platform decides; set it explicitly" and claims no default.
- **Where the OTel `gen_ai.*` telemetry lands on a native Agent Runtime deploy
  (2026-09-05, VERIFIED NEGATIVE).** Two control deploys were run: one with
  `--otel_to_cloud` (6.2) and one with `GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true`
  + both content knobs in `.env` (6.3). **What we confirmed:** each route writes
  the expected env vars to the deployment (the flag also adds
  `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`; the `.env` route adds only what
  `.env` carried), read back via the `vertexai` SDK
  (`engine.api_resource.spec.deployment_spec.env` — `gcloud ai reasoning-engines`
  does not exist in this install). The deployed agent answered queries and its
  framework INFO logs landed on `aiplatform.googleapis.com/reasoning_engine_stderr`.
  **What we could NOT confirm:** the `gen_ai.*` OTel events (which DO appear in
  Cloud Logging on local and Cloud Run runs, 5.2-5.5) did **not** surface in
  Cloud Logging under any `gen_ai.*` log name, and **no Cloud Trace spans**
  appeared for the engine across a 40-minute window and multiple queries. So on
  native Agent Runtime the telemetry destination is unresolved: it may require
  Console-side enablement, a longer export path than we waited for, or a wrapper
  exporter set we did not identify. Part 6 states only what was observed. Both
  control engines were deleted after the runs.

---

## References

- [ADK logging](https://adk.dev/observability/logging/) — log levels, the
  `google_adk` tree, content-capture env var.
- [ADK observability overview](https://adk.dev/observability/) — logging,
  tracing, metrics, integrations.
- [ADK traces](https://adk.dev/observability/traces/) and
  [ADK metrics](https://adk.dev/observability/metrics/) — the `OTEL_EXPORTER_OTLP_*`
  env-var route for CLI-launched servers (5.7).
- [ADK observability integrations](https://adk.dev/integrations/?topic=observability) —
  the vendor list (Honeycomb, Grafana, MLflow, …) for non-Google backends (5.7).
- [OTLP exporter configuration](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/) —
  the `OTEL_EXPORTER_OTLP_*` variable defaults ADK inherits.
- [Cloud Trace for ADK](https://adk.dev/integrations/cloud-trace/) — the span
  hierarchy and per-deployment setup.
- [Structured logging on Cloud Run](https://cloud.google.com/run/docs/logging) —
  the special JSON fields (`severity`, `logging.googleapis.com/trace`) Cloud
  Logging parses.
- [Agent Engine observability](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing) —
  where Reasoning Engine logs and traces land.

---

[← 6.4 · What the platform changes](part-6/6.4-platform-changes.md)<br>
[Tutorial index](../TUTORIAL.md)
