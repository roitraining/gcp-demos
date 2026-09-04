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

- The **Part 5 cloud export was run** against `jwd-gcp-demos` (2026-09-04) with
  [examples/08_otel_cloud.py](../examples/08_otel_cloud.py) in `cloud` mode, and
  the results confirmed end to end. Three findings: `maybe_set_otel_providers`
  needs a project-scoped `get_gcp_resource(project)` or the
  `telemetry.googleapis.com` endpoint rejects every span batch with a 400; the
  GenAI events land under `gen_ai.*` log names, not `adk-otel`; and the
  `NO_CONTENT` default was confirmed by reading a `gen_ai.user.message` entry
  back with its `content` field `<elided>`. The `invocation` spans appear in
  Cloud Trace, in the console Trace explorer and via the v1 `traces.list` API
  (query with a user token from `gcloud auth print-access-token` and
  `orderBy=start desc`).

Not verified here (documented, run them yourself):

- The `deploy/deploy_cloudrun.sh` deploy of the Part 4 custom server end to end.
  The formatter and trace correlation are verified locally (4.2); the
  containerized Cloud Run deploy of it (4.3) is not.

---

## References

- [ADK logging](https://adk.dev/observability/logging/) — log levels, the
  `google_adk` tree, content-capture env var.
- [ADK observability overview](https://adk.dev/observability/) — logging,
  tracing, metrics, integrations.
- [Cloud Trace for ADK](https://adk.dev/integrations/cloud-trace/) — the span
  hierarchy and per-deployment setup.
- [Structured logging on Cloud Run](https://cloud.google.com/run/docs/logging) —
  the special JSON fields (`severity`, `logging.googleapis.com/trace`) Cloud
  Logging parses.
- [Agent Engine observability](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/manage/tracing) —
  where Reasoning Engine logs and traces land.

---

← Prev: [6. Agent Runtime](06-agent-runtime.md) · [Tutorial index](../TUTORIAL.md)

