[← 4.6 · Metrics or rows](part-4/4.6-metrics-or-rows.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# How to choose

*The signal catalog, the store-choice decision, and what is verified. The last page.*

> [!NOTE]
> **Why you are here.** This page is a reference, not a lesson. Use it to find the
> right signal for a question, decide which store to send it to, and check what
> has been verified against a real run.

## Signal catalog

Each row is one operational question, the signal that answers it, and where that
signal lives. ADK emits six metric names for a single agent. A seventh,
`gen_ai.invoke_workflow.duration`, needs the `Workflow` primitive. PromQL files are in [queries/](../queries/);
row columns are in the `v_*` views the plugin builds.

| Question | Signal | Where | File / column |
|---|---|---|---|
| How slow is a turn? | `gen_ai.invoke_agent.duration` p50/p95 | Metrics | `queries/latency.promql` |
| How slow is the model? | `gen_ai.client.operation.duration` p95 by model | Metrics | `queries/latency.promql` |
| How slow is a tool? | `gen_ai.execute_tool.duration` p95 by tool | Metrics | `queries/latency.promql` |
| How many turns per minute? | `gen_ai.invoke_agent.duration` count | Metrics | `queries/volume.promql` |
| How much work per turn? | `inference_calls`, `tool_calls` sum ÷ count | Metrics | `queries/volume.promql` |
| How often does a tool fail? | `gen_ai.execute_tool.duration` with `error.type` | Metrics | `queries/errors.promql` |
| How often does a turn fail? | `gen_ai.invoke_agent.duration` with `error.type` | Metrics | `queries/errors.promql` |
| How many tokens, by type? | `gen_ai.client.token.usage` sum by `gen_ai.token.type` | Metrics | `queries/tokens.promql` |
| Did the task get done? | `tutorial.weather.requests` by `outcome` | Metrics | `queries/outcome.promql` |
| Which numbers are the workflow's? | `gen_ai.invoke_workflow.duration` by `gen_ai.workflow.name` (needs `Workflow`) | Metrics | Part 1, 1.5 |
| Which session cost the most? | `SUM(usage_total_tokens)` grouped by `session_id` | Rows | `v_llm_response` |
| Which prompt drove it? | `content` for the top invocation | Rows | `agent_events.content` |
| Which call was expensive, and cached? | tokens, `context_cache_hit_rate` per call | Rows | `v_llm_response` |
| What happened, step by step? | the whole invocation, replayed | Rows / SDK | `Client(project, dataset).get_trace(trace_id).render()` |

## Which store

Send a question to the store whose shape fits it. When both can answer, the tie
breaks on latency-to-visibility and cost.

| If you need… | Use | Why |
|---|---|---|
| An alert or a live dashboard | Cloud Monitoring | Seconds to visibility, native alerting, cheap per series |
| An aggregate at bounded cardinality | Cloud Monitoring | Histograms are built for "how much, how fast, how often" |
| A group-by on a session, user, or invocation | BigQuery | Unbounded ids are columns, never metric attributes |
| The prompt or response text | BigQuery | Content lives only in rows |
| A step-by-step replay of one turn | BigQuery SDK | `get_trace(trace_id).render()` reconstructs the invocation |
| Metrics somewhere other than Google | OTLP backend | Env-var route, http/protobuf only (Part 2) |

The two stores side by side:

| Dimension | Metrics (Cloud Monitoring) | Rows (BigQuery) |
|---|---|---|
| Latency to visibility | Seconds (5 s export) | Seconds (`batch_size=1`, flushed each run) |
| Cardinality | Bounded; no ids | Unbounded; every id is a column |
| Cost model | Per sample ingested ([pricing](https://cloud.google.com/products/observability/pricing)) | Per ingestion volume and per query scanned |
| Retention | 24 months ([Managed Service for Prometheus](https://docs.cloud.google.com/stackdriver/docs/managed-prometheus)) | As long as you keep the table |
| Content | None | Full prompt and response |
| Alerting | Native, on any series | Not built in; query on a schedule |
| Join key | `otel_scope_*`, attribute labels | `session_id`, `invocation_id`; `trace_id` to Cloud Trace |

The stores meet at Cloud Trace, not at each other: a metric carries no id, so the
only join is a row's `trace_id` to its trace. That needs span export in the agent
process, which `04_bq_plugin.py` turns on; `enable_otel_correlation=True` adds the
span ids under `attributes.otel` for a span-level join
([4.6](part-4/4.6-metrics-or-rows.md)).

## 2.8.0 versus head

The tutorial is verified against google-adk 2.8.0. The `adk-python` checkout ahead
of it moves per-invocation token totals into an `_AgentInvocationScope` and adds
skill-load histograms to the flush. Neither changes a metric name or the pages;
verify against 2.8.0 before relying on head.

## Verification status

Every output block is captured from a real run unless it is labeled illustrative.
Run records live in [verification/](../verification/).

### Verified

| Item | Evidence |
|---|---|
| Six `gen_ai.*` names on the console reader for a single agent | Part 1 runs, 2026-09-06; rerun 2026-10-02 |
| `error.type` on a tool needs the `_detect_error_in_response` hook | Part 1: two series, one `error.type=lookup_failed`, clean invocation |
| `adk.experimental.*` is gated on `ADK_EXPERIMENTAL_TELEMETRY` | 1.4 rerun, 2026-10-02: 12 names on, 6 off |
| `force_flush()` drains the reader under `shutdown_on_exit=False` | Stage 0 |
| Raw script export needs `gcp.project_id` on the resource | Stage 0: 400 without, 200 with; 2.4 rerun, 2026-10-02 |
| `adk web`, Cloud Run, your own server and Agent Runtime all export the six names | Part 2 captures; 2.3 to 2.5 rerun, 2026-10-02 |
| Cloud Run fills `location` with no `OTEL_RESOURCE_ATTRIBUTES` | 2.3 rerun on a dev project, 2026-10-02 |
| Agent Runtime metrics through `_RequestDrivenMetricReader` | 2.5 rerun, 2026-10-02: 10 of 10 turns exported |
| Export outage: turns answered, batches rejected, no new points | 2.1 deep dive rerun, 2026-10-02: count stayed at 20 |
| PromQL addresses dotted histograms as `_sum`/`_count`/`_bucket` in the brace form | Part 3 captures, 2026-10-02 |
| No second `gen_ai.client.*` scope in one process; token sums are not doubled | Stage 0: one scope, single counts |
| Overlapping turns keep tool timers; turn and model latency rise | 3.1 deep dive, 2026-10-02 |
| Dashboard and alert policy configs create through `gcloud`; the alert opens an incident | 3.5 and 3.6, 2026-10-02: incident at ratio 0.498 |
| `tutorial.weather.requests` reaches Cloud Monitoring as `/counter`, with no `_total` | 3.7, 2026-10-02: unavailable share 0.5 |
| Plugin creates `agent_events` and all 25 `v_*` views | Part 4 rerun, 2026-10-02 |
| Row token sums match the histogram: input exactly, output as completion plus thinking | Part 4 rerun: 22,093 input both sides; 1,645 = 608 + 1,037 |
| SDK 0.5.2 `get_trace()` takes a `trace_id`; `error_rate` counts only raised tool errors | Part 4 rerun: render captured; 0 errors on `unknown-city` |
| A row's `trace_id` opens its trace in Cloud Trace when the process exports spans | Part 4 rerun: 32 s turn read back from Cloud Trace |

### Not verified

| Item | Gate |
|---|---|
| Looker Studio template opens on `agent_events` | 4.5 is a browser workflow |
| Non-Google OTLP backends | 2.6 is a reference page; no backend was available |

## References

- [ADK observability documentation](https://adk.dev/observability/): the meter,
  the export routes, and backends.
- [OpenTelemetry GenAI metrics semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/):
  `gen_ai.client.token.usage` and `gen_ai.client.operation.duration`.
- [Cloud OTLP metric ingestion](https://docs.cloud.google.com/stackdriver/docs/otlp/overview):
  the `prometheus.googleapis.com/<name>/<point kind>` naming rule.
- [BigQuery Agent Analytics SDK](https://github.com/GoogleCloudPlatform/BigQuery-Agent-Analytics-SDK):
  the plugin's companion SDK and the Looker Studio template.
- [SigNoz dashboards](https://github.com/SigNoz/dashboards): a Google ADK panel
  list that maps onto ADK's own metrics.

---

[← 4.6 · Metrics or rows](part-4/4.6-metrics-or-rows.md)<br>
[Tutorial index](../TUTORIAL.md)
