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
signal lives. Metric names are the seven ADK emits (six for a single agent; the
workflow duration needs a workflow). PromQL files are in [queries/](../queries/);
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
| Which numbers are the workflow's? | `gen_ai.invoke_workflow.duration` by `gen_ai.workflow.name` | Metrics | Part 1, 1.5 |
| Which session cost the most? | `SUM(usage_total_tokens)` grouped by `session_id` | Rows | `v_llm_response` |
| Which prompt drove it? | `content` for the top invocation | Rows | `agent_events.content` |
| Which call was expensive, and cached? | tokens, `context_cache_hit_rate` per call | Rows | `v_llm_response` |
| What happened, step by step? | the whole invocation, replayed | Rows / SDK | `Client().get_trace().render()` |

## Which store

Send a question to the store whose shape fits it. When both can answer, the tie
breaks on latency-to-visibility and cost.

| If you need… | Use | Why |
|---|---|---|
| An alert or a live dashboard | Cloud Monitoring | Seconds to visibility, native alerting, cheap per series |
| An aggregate at bounded cardinality | Cloud Monitoring | Histograms are built for "how much, how fast, how often" |
| A group-by on a session, user, or invocation | BigQuery | Unbounded ids are columns, never metric attributes |
| The prompt or response text | BigQuery | Content lives only in rows |
| A step-by-step replay of one turn | BigQuery SDK | `get_trace().render()` reconstructs the invocation |
| Metrics somewhere other than Google | OTLP backend | Env-var route, http/protobuf only (Part 2) |

The stores meet at Cloud Trace, not at each other: a metric carries no id, so the
only join is a row's `trace_id` to its trace. That needs span export in the agent
process, which `04_bq_plugin.py` turns on; `enable_otel_correlation=True` adds the
span ids under `attributes.otel` for a span-level join
([4.6](part-4/4.6-metrics-or-rows.md)).

## 2.8.0 versus head

The tutorial is verified against google-adk 2.8.0. The `adk-python` checkout ahead
of it differs in two ways that do not change any metric name or the pages:

- Per-invocation token totals move into an `_AgentInvocationScope`, and skill-load
  histograms join the flush.
- The names above are unchanged; verify against 2.8.0 before relying on head.

## Verification status

Every output block is a capture from a real run unless it is marked
`NEEDS-RUN`. As of 2026-10-02 those markers remain on 3.2, 3.3, 3.5, and 3.6;
Part 4 was re-run live with tracing on, except the Looker Studio page (4.5). The
authoritative status board is the plan at `docs/adk-metrics-tutorial.md`.

### Verified

| Item | Evidence |
|---|---|
| Six `gen_ai.*` names on the console reader for a single agent | Stage 1 run, 2026-09-06 |
| `error.type` on a tool needs the `_detect_error_in_response` hook | Stage 1: two series, one `error.type=lookup_failed`, clean invocation |
| `force_flush()` drains the reader under `shutdown_on_exit=False` | Stage 0 |
| PromQL addresses dotted histograms as `_sum`/`_count`/`_bucket` in the brace form | Stage 0 read-back |
| No second `gen_ai.client.*` scope; token sums are not doubled | Stage 0: one scope, single counts |
| `adk.experimental.*` is gated on `ADK_EXPERIMENTAL_TELEMETRY` | Stage 0 |
| Raw script export needs `gcp.project_id` in `OTEL_RESOURCE_ATTRIBUTES` | Stage 0: 400 without, 200 with |
| Plugin creates `agent_events` and all 25 `v_*` views on first write | Stage 4, 2026-10-02 |
| Row token sums match the histogram: input exactly, output as completion plus thinking | Stage 4: 22,874 input both sides; 1,778 = 616 + 1,162 |
| SDK 0.5.2 `get_trace()` takes a `trace_id`; `error_rate` counts only raised tool errors | Stage 4: render captured; 0 errors on `unknown-city` |
| A row's `trace_id` opens its trace in Cloud Trace when the process exports spans | Stage 4: 206 s turn read back, 204 s in one model call |

### Not verified

| Item | Gate |
|---|---|
| Cloud Run resource labels from the detector, no `OTEL_RESOURCE_ATTRIBUTES` | Part 2 (2.3) |
| Agent Runtime metrics through `_RequestDrivenMetricReader` | Part 2 (2.5) |
| Export outage: turns answered, batches rejected, no points | Part 2 (2.1 deep dive) |
| Overlapping turns do not cross timers | Part 3 (3.1 deep dive) |
| `tutorial.weather.requests` reaches Cloud Monitoring as `/counter` | Part 3 (3.7) |
| PromQL alert policy opens an incident | Part 3 (3.6) |
| Looker Studio template opens on `agent_events` | Part 4 (4.5) |

## References

- ADK metrics documentation (adk.dev): the meter, the export routes, and backends.
- OpenTelemetry GenAI semantic conventions: `gen_ai.client.token.usage` and
  `gen_ai.client.operation.duration`, the two stable-semconv metrics.
- Cloud OTLP metric ingestion overview (docs.cloud.google.com): the
  `prometheus.googleapis.com/<name>/<point kind>` naming rule.
- BigQuery Agent Analytics: the plugin, the `bigquery-agent-analytics` SDK, and the
  Looker Studio template.
- SigNoz ADK dashboard (github.com/SigNoz/dashboards): a panel list that maps onto
  ADK's own metrics.

---

[← 4.6 · Metrics or rows](part-4/4.6-metrics-or-rows.md)<br>
[Tutorial index](../TUTORIAL.md)
