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
| Emitting structured events you can query and alert on | Custom `BasePlugin` (4.1) | Real `logging` records; queryable, alertable. |
| Logging or guarding one agent only | Per-agent callback (4.4) | Siloed by design; can short-circuit a step. |
| Running your own HTTP server | `dictConfig` + the 4.1 plugin (4.2) | Own streams 1–3 in one place. |
| Seeing raw logs reach the cloud, fast | Cloud Run Job/service, no JSON (1.4, 1.5) | Zero setup; but severity is `DEFAULT` (unset), not yours. |
| Deploying to Cloud Run for real | JSON to stdout + trace field (4.3) | Auto-ingested; severity you set; grouped by request. |
| Deploying the agent to Agent Runtime | `adk deploy agent_engine` (1.6) + `--otel_to_cloud` | Managed; but the platform owns log format/stream. Telemetry did not surface in our runs; see Not verified. |
| Keeping your own logging on Agent Runtime | Custom container / BYOC (1.7) | Your server, your format; you implement the runtime contract. |
| Finding where latency goes | `--otel_to_cloud` / `get_gcp_exporters` | Timed span tree in Cloud Trace. |
| Silencing health-check access lines | A filter on `uvicorn.access` (Part 2) | The log level never reaches stream 3. |

Best-practice summary:

- Serve at **INFO or WARNING** in production; keep DEBUG for active debugging.
- Write one JSON object per line to stdout, with an explicit `severity`. Do not
  rely on Cloud Run inferring severity from the stream: 1.4 and 1.5 showed plain
  stderr lines landing as Default.
- Correlate with the **trace** field so a request is one filterable group.
- Turn content capture off in both places:
  `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT` for log events
  and `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` for span attributes (5.6).
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

See the [ADK observability docs](https://adk.dev/observability/).

---

## OpenTelemetry setup details

The setup behind [5.2](part-5/5.2-otel-to-cloud.md)'s `--otel_to_cloud` steps:
credentials and roles, the local metrics workaround, and why the settings must
be shell exports.

### Which roles and packages does the flag need?

**Where the credentials and project come from.** The flag's branch starts with
`google.auth.default()`, which returns both (`cli/api_server.py:680-718`, the
call at `:700`). That call takes the project from `GOOGLE_CLOUD_PROJECT` in the
shell when set, and from your gcloud configuration otherwise
(`google/auth/_default.py:698-720`). `demo_agent/.env` has not been loaded yet at
that point.

**Where each signal goes.** Spans and metrics leave through
`https://telemetry.googleapis.com/v1/traces` and `/v1/metrics`
(`telemetry/google_cloud.py:57-69`). The GenAI events go through the Cloud
Logging API (`:264-281`).

**Roles.** The
[Telemetry API overview](https://docs.cloud.google.com/stackdriver/docs/reference/telemetry/overview)
names `roles/telemetry.writer` on the project and
`roles/serviceusage.serviceUsageConsumer` on the quota project. The metrics
request captured in this session carried an `x-goog-user-project` header, so the
quota project matters even when it is the same project. `gcloud iam roles
describe` shows what the candidate roles carry:

| Role | Permissions it carries | Covers |
|---|---|---|
| `roles/telemetry.writer` | `telemetry.traces.write`, `monitoring.timeSeries.create`, `logging.logEntries.create` | all three signals |
| `roles/telemetry.tracesWriter` | `telemetry.traces.write` | spans only |
| `roles/telemetry.metricsWriter` | `monitoring.timeSeries.create` | metrics only |
| `roles/cloudtrace.agent` | `cloudtrace.traces.patch`, `telemetry.traces.write` | spans, via the older Cloud Trace role |
| `roles/logging.logWriter` | `logging.logEntries.create`, `logging.logEntries.route` | the `gen_ai.*` events |

5.2 was run as a project owner, so the minimal set was not exercised.
The table tells you which permission a `403` is complaining about.

**Packages.** `google-adk[otel-gcp]` (see [What does the otel-gcp extra add?](part-5/5.2-otel-to-cloud.md#what-does-the-otel-gcp-extra-add)),
`opentelemetry-exporter-otlp-proto-http` for spans and metrics, and
`opentelemetry-exporter-gcp-logging` for the events. That last import is
unguarded (`telemetry/google_cloud.py:272`), so it is not optional once the flag
is on.

### Why do metrics need `OTEL_RESOURCE_ATTRIBUTES`?

5.2 was first run without that export. Spans and events exported fine,
and the terminal filled with one of these every 5 seconds for as long as the
server ran:

```console
2026-09-04 17:21:03,454 - ERROR - __init__.py:294 - Failed to export metrics batch code: 400, reason: Bad Request
2026-09-04 17:21:08,556 - ERROR - __init__.py:294 - Failed to export metrics batch code: 400, reason: Bad Request
```

The OTLP exporter logs the status and reason and throws the body away
(`opentelemetry/exporter/otlp/proto/http/metric_exporter/__init__.py:294`).
Captured with a wrapped session, the body says:

```console
{"errors":[{"code":"INVALID_ARGUMENT","error_message":"prometheus_target resource type must have an instance specified","num_data_points":1,"example_resource_attributes":{"gcp.project_id":"jwd-gcp-demos"}}]}
```

The Telemetry API stores OTLP metrics as `prometheus_target` time series. That
monitored resource requires an `instance` and a real `location`, which the API
derives from `service.instance.id` and `cloud.region`. Off Agent Runtime,
`get_gcp_resource` starts from `{gcp.project_id}` and merges two detectors
(`telemetry/google_cloud.py:335-352`): the OTel one reads
`OTEL_RESOURCE_ATTRIBUTES` and `OTEL_SERVICE_NAME`, and the Google Cloud one
reads the metadata server, which a laptop does not have. So the resource is the
project id alone, exactly as `example_resource_attributes` shows, and every batch
is rejected.

Narrowing it down one attribute at a time:

| Resource attributes | Result |
|---|---|
| `service.instance.id` alone | `write for resource failed: Unrecognized region or location.` |
| plus `cloud.region=global` | `location / region / zone label cannot be set to "global"` |
| plus `cloud.region=us-central1` | `200` |

`cloud.region` must be a real region, not the model's region and not `global`.
On Cloud Run and Agent Runtime the resource detector supplies a region and
instance from the metadata server, so the variable is not needed there.

### Why can `.env` not set these?

Neither the flag nor the `OTEL_*` variables can come from the agent's `.env`.
The agent's `.env` is loaded when the agent itself is first loaded
(`cli/utils/agent_loader.py:331-332`), on the first request that needs it. The
exporters were chosen, and the knobs read, when the server object was built, in
`_setup_telemetry` (`cli/api_server.py:1173-1179`), before any request existed.
The only branch that reads `.env` at startup belongs to the older
`--trace_to_cloud` flag (`cli/fast_api.py:312-328`), which the source marks for
removal.

The server log shows the order, trimmed to the lines that matter:

```console
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:49686 - "GET /list-apps HTTP/1.1" 200 OK
2026-09-04 18:48:07,909 - INFO - api_server.py:1092 - New session created: s5-knob
INFO:     127.0.0.1:49693 - "POST /apps/demo_agent/users/u1/sessions/s5-knob HTTP/1.1" 200 OK
2026-09-04 18:48:07,931 - INFO - envs.py:83 - Loaded .env file for demo_agent at /Users/jeff/Desktop/Dev/gcp-demos/ai/adk/logging/demo_agent/.env
2026-09-04 18:48:07,933 - INFO - agent_loader.py:188 - Found root_agent in demo_agent.agent
```

Startup completed, requests were served, a session was created, and only then,
on the first `/run`, was `.env` read. Anything decided before that point comes
from the command line or the shell. The exporter endpoint variables in 5.7 are
the same story. On your own server (5.5) you control the order, and `.env`
works.

---

## Verification status

All runs were against real projects with Vertex AI and Gemini 3.7 Flash. Every
console block was captured from one of these runs on `jwd-gcp-demos`, except the
items under Not verified.

| Section | What ran | Date | What it showed |
|---|---|---|---|
| 1.1–1.3, 3.1, 3.3, 4.1, 4.2 | Examples 01–06 locally | 2026-10-02 | DEBUG/INFO/WARNING differences, plugin narration, JSON events with explicit `severity` and the trace field. |
| Part 2 | `02_tame_uvicorn.py` locally | 2026-08-31 (rerun matched 2026-10-02) | Health checks filtered from `uvicorn.access`. |
| 1.4, 1.5 | Cloud Run Job and service | 2026-10-02 | stderr lands as Default, not ERROR. |
| 1.6, 1.7 | Native Agent Runtime and a BYOC container | 2026-10-02 | The platform owns the format natively; BYOC keeps yours. Both log to `reasoning_engine_stderr`. |
| 3.2, 3.4 | `deploy/deploy_plugin_job.sh` | 2026-10-02 | Plugin narration survives `LOG_LEVEL=WARNING` with Default severity (3.2). The YAML survives on a mounted bucket, and the plugin warns about the mount's mode (3.4). |
| 4.3 | `deploy/deploy_cloudrun.sh` | 2026-10-02 | Eight `jsonPayload` rows per question at `INFO`; plugin fields queryable. |
| 5.1 | plain `adk web` | 2026-09-04 | The five span names from the session trace endpoint the Trace tab reads. |
| 5.2 | `adk web --otel_to_cloud` | 2026-09-04, captures 2026-09-05 | `gen_ai.*` events in Cloud Logging in both formats. Local metrics need `OTEL_RESOURCE_ATTRIBUTES`. |
| 5.3 | `adk api_server --otel_to_cloud` | 2026-10-02 | Two `operation.details` events per turn, content off. |
| 5.4 | `adk deploy cloud_run --otel_to_cloud` | 2026-10-02 | Eight default-format events on `generic_task` (job = service name), content elided by default. |
| 5.5 | `08_otel_server.py` locally and on Cloud Run | 2026-10-02 | Locally, `generic_task` with job `weather-agent` once `service.instance.id` is set. On Cloud Run, `generic_node` with no job. |
| 6.2, 6.3 | Two Agent Runtime deploys (flag, `.env`) | 2026-10-02 | Each route writes the expected env vars; framework INFO lines on `reasoning_engine_stderr`; no `gen_ai.*` events. |

**Not verified or inconclusive.** Documented from the source, or checked
without a clear result; run them yourself.

| Item | What is missing |
|---|---|
| 5.2 span-content check (Steps 5-6, Trace Explorer) | The source answers it: `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS` defaults to on and `=false` writes `{}` to `gcp.vertex.agent.llm_request` (`telemetry/tracing.py:629-635`). Not yet observed in Trace Explorer. |
| The Part 4 plugin on Agent Runtime | Part 6 says the plugin works unchanged on a native deploy; no page runs it there. |
| Agent Runtime with no flag and no `.env` variable | Whether such a deploy produces traces. Every native deploy here passed the flag or set the var. |
| Where native Agent Runtime OTel telemetry lands (checked 2026-09-05 and 2026-10-02, nothing found) | No `gen_ai.*` log names and no Cloud Trace spans appeared for the engine. Part 6 states only what was observed. |

To rerun Part 5, follow 5.2's exports.

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
