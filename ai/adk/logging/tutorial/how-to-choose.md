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
- Emit **one JSON object per line** with an explicit **`severity`**, to
  **stdout**. Do not rely on Cloud Run inferring severity from the stream: 1.4
  and 1.5 showed plain stderr lines landing as Default.
- Correlate with the **trace** field so a request is one filterable group.
- Keep GenAI content capture at **`NO_CONTENT`** unless you have a reviewed reason.
- Tune the framework as a group via `logging.getLogger("google_adk")`, and
  silence `uvicorn.access` health-check spam.
- Remember which stream a flag configures. Most confusion is a flag aimed at the
  wrong stream.

---

## Beyond logging

This tutorial stopped at logging and the log-facing side of tracing. The wider
observability story:

- **Cloud Trace** spans (Part 5) for latency breakdowns across `call_llm` and
  `execute_tool`.
- **BigQuery Agent Analytics** (`BigQueryAgentAnalyticsPlugin`) logs structured
  agent events to BigQuery for conversational analytics and LLM-as-judge evals.
- **Third-party platforms** (AgentOps, Phoenix, MLflow, Weave, and others)
  integrate over OpenTelemetry for session replays and dashboards.

The ADK observability skill and `https://adk.dev/observability/` cover these.

---

## Verification status

All runs were against one real project (`jwd-gcp-demos`, Vertex AI, Gemini 3.7
Flash). Every console block in the tutorial is from one of these runs.

| Section | What ran | Date | What it showed |
|---|---|---|---|
| 1.1–1.3, 3.1, 3.3, 4.1, Part 2 | Examples 01–09 locally | | DEBUG/INFO/WARNING differences, plugin narration, JSON events. |
| 4.2 | `06_custom_server.py` locally | 2026-09-04 | Every stream emits JSON with explicit `severity`, and with the `X-Cloud-Trace-Context` header, the same `logging.googleapis.com/trace` value. |
| 1.4, 1.5, 1.6 | Cloud Run Job, Cloud Run service, native Agent Runtime, BYOC container | 2026-09-03 | stderr lands as Default, not ERROR (1.4, 1.5). The platform owns the format on native Agent Runtime (1.6). The `artifactregistry.reader` and reserved-var traps (1.6 BYOC). |
| 3.2, 3.4, Part 4 Job | `deploy/deploy_plugin_job.sh` | 2026-09-03 | Narration survives `LOG_LEVEL=WARNING` and lands on stdout with Default severity and literal ANSI bytes (3.2). The YAML is discarded with the container until a Cloud Storage volume is mounted, and the plugin then warns about the FUSE mount's mode (3.4). The Part 4 plugin's JSON parsed into queryable `jsonPayload` fields with `severity` INFO. |
| 5.1 | plain `adk web` | 2026-09-04 | Seven spans read back from `/dev/apps/demo_agent/debug/trace/session/{id}`, the endpoint the Trace tab reads. `adk api_server` installs the same exporters but serves no `/dev` route (404), so [otel/check_local.sh](../otel/check_local.sh) uses `adk web`. |
| 5.2 | `adk web --otel_to_cloud` | 2026-09-04, captures 2026-09-05 | Exported to Cloud Trace, Cloud Logging (`gen_ai.*`), and Cloud Monitoring. OTLP metrics land as `prometheus.googleapis.com/gen_ai.*` on `prometheus_target` and need `OTEL_RESOURCE_ATTRIBUTES` locally or every batch returns 400. `google-adk[otel-gcp]` does not duplicate the `generate_content` span. The log-side blocks in Steps 1, 2, 4, and 5 are real captures (traces `c5fdba98…`, `9d24673b…`, `3b80ad2b…`, `acacdad7…`). |
| 5.3 | `adk api_server --otel_to_cloud` | 2026-09-04 | The original run produced the same tree (trace `fb802902…`). The rewritten three-export version has not been re-run. |
| 5.4 | `adk deploy cloud_run --otel_to_cloud ./demo_agent` | 2026-09-04 | `gen_ai.*` on a `generic_task` resource (job = service name), content `<elided>` proving `demo_agent/.env`'s span knob shipped in the image. No `OTEL_RESOURCE_ATTRIBUTES` needed on Cloud Run. A bare `google-adk` container boot-crashes at the OTLP exporter import. Service deleted after the run. |
| 5.5 (local) | `examples/08_otel_server.py` | 2026-09-05 | `gen_ai.*` events on `generic_task` with `resource.labels.job` = `weather-agent`. Content knob verified through `.env` both ways (`true` shows prompt text, `NO_CONTENT` shows `<elided>`). Logging-only export needs no `get_gcp_resource`; the exporter takes the project from ADC. |
| 6.2, 6.3 | Two control Agent Runtime deploys (flag route, `.env` route) | 2026-09-05 | Each route writes the expected env vars, read back via the `vertexai` SDK (`engine.api_resource.spec.deployment_spec.env`; `gcloud ai reasoning-engines` does not exist in this install). The agent answered queries and its framework INFO logs landed on `reasoning_engine_stderr`. Both engines deleted after the runs. |

**Not verified.** Documented from the source; run them yourself.

| Item | What is missing |
|---|---|
| 5.2 span-content check (Steps 2-3, Trace Explorer) | Whether `=true` also puts the prompt and reply on the `call_llm` span's `gcp.vertex.agent.llm_request` / `llm_response`, and whether `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` empties them while the logs keep content. |
| 5.3 rewritten run | `adk api_server --otel_to_cloud` with the three shell exports, the London turn over curl, and `gen_ai.*` read back. The page shows no output blocks pending this run. |
| 5.5 Cloud Run deploy | The inline `gcloud run deploy --source` path and `deploy/Dockerfile.otel_server` are written but not deployed. |
| 4.3 end to end | The formatter and trace correlation are verified locally (4.2); the containerized `deploy/deploy_cloudrun.sh` deploy is not. |
| Agent Runtime with no flag and no `.env` variable | Whether such a deploy produces traces. Every deploy here passed the flag or set the var. Part 6 says "the platform decides; set it explicitly" and claims no default. |
| Where native Agent Runtime OTel telemetry lands (**verified negative**, 2026-09-05) | The `gen_ai.*` events that appear on local and Cloud Run runs (5.2-5.5) did **not** surface under any `gen_ai.*` log name, and **no Cloud Trace spans** appeared for the engine across a 40-minute window and multiple queries. It may require Console-side enablement, a longer export path, or a wrapper exporter set not identified here. Part 6 states only what was observed. |

**Re-run checklist for Part 5:** `gcloud auth application-default login`; enable
`telemetry.googleapis.com`; `export OTEL_RESOURCE_ATTRIBUTES=…` for a local
`--otel_to_cloud` run; keep the `.env` knob line; prompt "What's the weather in
London?".

---

## References

- [ADK logging](https://adk.dev/observability/logging/): log levels, the
  `google_adk` tree, content-capture env var.
- [ADK observability overview](https://adk.dev/observability/): logging,
  tracing, metrics, integrations.
- [ADK traces](https://adk.dev/observability/traces/) and
  [ADK metrics](https://adk.dev/observability/metrics/): the `OTEL_EXPORTER_OTLP_*`
  env-var route for CLI-launched servers (5.7).
- [ADK observability integrations](https://adk.dev/integrations/?topic=observability):
  the vendor list (Honeycomb, Grafana, MLflow, …) for non-Google backends (5.7).
- [OTLP exporter configuration](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/):
  the `OTEL_EXPORTER_OTLP_*` variable defaults ADK inherits.
- [Cloud Trace for ADK](https://adk.dev/integrations/cloud-trace/): the span
  hierarchy and per-deployment setup.
- [Structured logging on Cloud Run](https://cloud.google.com/run/docs/logging):
  the special JSON fields (`severity`, `logging.googleapis.com/trace`) Cloud
  Logging parses.
- [Agent Engine observability](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing):
  where Reasoning Engine logs and traces land.

---

[← 6.4 · What the platform changes](part-6/6.4-platform-changes.md)<br>
[Tutorial index](../TUTORIAL.md)
