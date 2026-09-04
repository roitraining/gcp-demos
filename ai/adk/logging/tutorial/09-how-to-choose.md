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
| Emitting metrics for production | Custom `BasePlugin` (Part 4) | Real `logging` records; queryable, alertable. |
| Logging or guarding one agent only | Per-agent callback (4.1) | Siloed by design; can short-circuit a step. |
| Running your own HTTP server | `dictConfig` + the Part 4 plugin | Own all four streams in one place. |
| Seeing raw logs reach the cloud, fast | Cloud Run Job/service, no JSON (1.4, 1.5) | Zero setup; but severity is Cloud Run's guess (Default), not yours. |
| Deploying to Cloud Run for real | JSON to stdout + trace field (Part 6) | Auto-ingested; severity you set; grouped by request. |
| Deploying the agent to Agent Runtime | `adk deploy agent_engine` (1.6) + `--otel_to_cloud` | Managed; but the platform owns log format/stream. |
| Keeping your own logging on Agent Runtime | Custom container / BYOC (1.7) | Your server, your format; you implement the runtime contract. |
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

- **Cloud Trace** spans (Part 7) are worth exploring on their own for latency
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

- Examples 01 through 08 all run; every console block above is captured from a
  real run.
- Part 1's DEBUG/INFO/WARNING differences, Part 3's plugin narration, Part 4's
  JSON events, Part 5's server, and Part 6's trace correlation are all reproduced
  as shown.
- Example 08 `cloud` mode exports to Cloud Trace and Cloud Logging without error
  via application-default credentials.
- The **cloud deploys in 1.4-1.7 were all run** against `jwd-gcp-demos`
  (2026-09-03) and every console block in those sections is captured from the
  real run: the Cloud Run Job (1.4), the Cloud Run service (1.5), the native
  Agent Runtime agent (1.6), and the custom container / BYOC (1.7). The findings
  that differ from common advice, stderr landing as Default not ERROR (1.4/1.5),
  the platform owning log format on native Agent Runtime (1.6), the project-level
  `artifactregistry.reader` and reserved-var model-region traps (1.7), are all
  from those runs.
- The **plugin Cloud Run Jobs in 3.2, 3.4, and 4 were run** against `jwd-gcp-demos`
  (2026-09-03) with [deploy/deploy_plugin_job.sh](../deploy/deploy_plugin_job.sh).
  3.2's two findings (the narration survives `LOG_LEVEL=WARNING` untouched; it
  lands on stdout with Default severity and literal ANSI bytes) and 3.4's (the
  YAML is discarded with the container until a Cloud Storage volume is mounted,
  and the plugin then emits its mode-600 warning against the FUSE mount) are both
  from those runs. Part 4's Job confirmed the structured payoff: the plugin's JSON
  parsed into queryable `jsonPayload` fields (`event`, `tool`, `latency_ms`,
  `status`) and its `severity` landed as `INFO`, not Default.

Not verified here (documented, run them yourself):

- The Part 6/7 `deploy/deploy_cloudrun.sh` structured-JSON deploy and the
  `--otel_to_cloud` telemetry export end to end. The 07 formatter and trace
  correlation are verified locally (Part 6 body); the containerized deploy of it
  is not.
- Reading the exported `adk-otel` entries back with `gcloud logging read`
  (needs an interactive `gcloud auth login` in your shell).

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

← Prev: [8. Agent Runtime](08-agent-runtime.md) · [Tutorial index](../TUTORIAL.md)

