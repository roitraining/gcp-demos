[← 4.6 · Cost, retention, and content policy](part-4/4.6-cost-retention-content.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# How to choose & reference

*The span catalog, the failure and correlation decisions, the version caveats, and what was verified. The last page.*

> [!NOTE]
> **Why you are here.** This page is a reference, not a lesson. Use it to look up
> a span or attribute, pick a correlation setup, and check what has been verified
> against a real run on google-adk 2.8.0.

## Span catalog

Every row was read back from a real run on 2.8.0 unless marked source only. The
single-tool baseline turn is seven spans with five names:

```
invocation
  invoke_agent weather_agent
    call_llm
      generate_content gemini-3.7-flash
      execute_tool get_weather
    call_llm
      generate_content gemini-3.7-flash
```

| Span | Parent | Key attributes | Page |
|---|---|---|---|
| `invocation` | none (root, schema v1) | none | [1.1](part-1/1.1-the-tree-you-already-have.md) |
| `invoke_agent {agent}` | `invocation` | `gen_ai.operation.name`, `gen_ai.agent.name`, `gen_ai.conversation.id` (equals the session id) | [1.5](part-1/1.5-a-trace-per-turn.md) |
| `call_llm` | `invoke_agent` | `gen_ai.system=gcp.vertex.agent`, `gen_ai.request.model`, `gcp.vertex.agent.{session_id, invocation_id, event_id, llm_request, llm_response}` | [1.3](part-1/1.3-attributes-and-content.md) |
| `generate_content {model}` | `call_llm` | `gen_ai.request.model`, `gen_ai.conversation.id`; the `gen_ai.*` log events carry this span's id | [3.1](part-3/3.1-the-free-join.md) |
| `execute_tool {tool}` | the `call_llm` that emitted the function call | `gen_ai.tool.name`, `gen_ai.tool.type`, `gen_ai.tool.call.id`, `gen_ai.agent.name`, `gcp.vertex.agent.{tool_call_args, tool_response, event_id}`; `error.type` when classified or raised | [1.2](part-1/1.2-the-raw-span.md), [1.4](part-1/1.4-an-error-turn-three-ways.md) |
| `fetch_forecast` (yours) | `execute_tool get_forecast` | `forecast.days` | [1.6](part-1/1.6-your-own-span-inside-a-tool.md) |
| `invoke_workflow {agent}` | none (root, schema v2, Agent Runtime) | `gen_ai.operation.name=invoke_workflow`, `gen_ai.workflow.name`; `call_llm` still present below it | [2.4](part-2/2.4-agent-runtime.md) |
| `POST /chat`, plus `http receive` and two `http send` | the inbound `traceparent` | from `FastAPIInstrumentor`; `invocation` becomes a child of `POST /chat` | [3.4](part-3/3.4-one-trace-per-request.md) |
| `/chat` (Cloud Run) | external | only on a request Cloud Run sampled; the request log's `spanId` | [3.4](part-3/3.4-one-trace-per-request.md) |
| `execute_tool (merged)` | `invoke_agent` | parallel tool calls only; source only (`google/adk/flows/llm_flows/functions.py:526`, `:774`) | none |

Three facts that trip readers:

- `call_llm` #1 contains the tool, so compare model time on `generate_content`, not `call_llm` ([4.1](part-4/4.1-the-slow-step.md)).
- `gen_ai.conversation.id` is on `invoke_agent` and both `generate_content` spans; `call_llm` carries the same value as `gcp.vertex.agent.session_id` ([4.2](part-4/4.2-one-users-request.md)).
- `gcp.vertex.agent.llm_request` on `execute_tool` is always `{}`; the prompt is on `call_llm`.

## Tool-failure shapes

The Atlantis turn, four ways ([1.4](part-1/1.4-an-error-turn-three-ways.md);
the `{"error": ...}` row is a throwaway tool tried before the pages were
written). Only the last three leave a mark on the span.

| Tool behavior | `execute_tool` status | `error.type` | Exception events | Parents | User answer |
|---|---|---|---|---|---|
| returns `{"status": "error", ...}`, plain `FunctionTool` | UNSET | none | none | UNSET | "no data" |
| returns `{"error": ...}`, plain `FunctionTool` | ERROR | `TOOL_ERROR` | none | not captured | not captured |
| returns the status dict through the `StatusAwareTool` hook | ERROR, description `lookup_failed` | `lookup_failed` | none | UNSET | "no data" |
| raises `LookupError` | ERROR | `LookupError` | two, both `LookupError` (ADK's, then OpenTelemetry's on span exit) | `invoke_agent` and `invocation` ERROR, one exception event each; five spans in all | none; the request fails |

Rules behind the table:

- `FunctionTool`'s own hook returns `TOOL_ERROR` for a dict with a truthy `error` key (`google/adk/tools/function_tool.py:355-359`).
- `error.type` comes from an `error_type` attribute, then a genai `APIError` code, then the class name (`google/adk/telemetry/tracing.py:177-192`). `error.type` holds only the class name. The status description holds the full message (`LookupError: No weather data for 'Atlantis'.`), and each `exception` event stores the message and stack trace (`google/adk/telemetry/tracing.py:281`), so the city name does land on the span.
- The v1 API exposes no span status, so `error.type` is the only error handle a script can filter on ([4.3](part-4/4.3-the-failed-step.md)).

## Correlation

A log entry shows under a span when its top-level `trace` and `spanId` match a
span stored in the same project ([3.1](part-3/3.1-the-free-join.md)).

| Setup | `gen_ai.*` events | Your and `google_adk` lines | Request-level line | Cloud Run `request_log` |
|---|---|---|---|---|
| `02`: exporters, no bridge | under `generate_content` | no `trace` | no `trace` | different trace id ([2.2](part-2/2.2-cloud-run.md)) |
| `03`: + way A bridge | under `generate_content` | under the span current at emit time | no span to stamp | different trace id |
| `04`: + `FastAPIInstrumentor` + `always_on` | under `generate_content` | under their spans | under `POST /chat` | same trace string; joins (2.8.0) |

| Decision | Choose | Why |
|---|---|---|
| Which bridge | way A, OTel `LoggingHandler` on the root logger | same exporter as the `gen_ai.*` events; works on a laptop ([3.5](part-3/3.5-three-ways-to-stamp.md)) |
| Which propagator | W3C `traceparent` | Cloud Run always sends it and keeps an inbound one; add the GCP format only for callers that send `X-Cloud-Trace-Context` alone |
| Which sampler with propagation | `OTEL_TRACES_SAMPLER=always_on` | the default `ParentBased(ALWAYS_ON)` records zero spans under an unsampled parent ([3.4](part-3/3.4-one-trace-per-request.md)) |
| Which log name | `GOOGLE_CLOUD_DEFAULT_LOG_NAME` (`env.sh` sets it to the service name) | otherwise bridged lines land under `adk-otel` |

## Content settings

The two content variables, their defaults, the always-redacted payloads, and
the deploy defaults are in
[4.6 · Cost, retention, and content policy](part-4/4.6-cost-retention-content.md#what-should-never-be-in-a-span).
With both defaults, the only prompt text Cloud Trace holds is on the spans.
Whether the **Inputs/Outputs** tab renders it is not verified.

## Trace v1 API gotchas

| Gotcha | What to do |
|---|---|
| `spanId` and `parentSpanId` are decimal uint64; log entries use 16 hex | convert with `int(hex, 16)` before comparing |
| A new trace 404s with "Trace bucket not found" for 20 to 120 s | retry; `get_trace.sh` does |
| Filter terms split on spaces | quote span names: `span:"execute_tool get_forecast"` |
| An unfiltered list can return an empty first page | always pass a filter |
| `orderBy=duration` and `latency:` act on the root span only | use the **Grouped** tab for per-span percentiles |
| No status field | filter on `error.type:<value>` |
| Lists come back ordered by trace id | sort by start time yourself |
| 300 reads per minute per project; a 429 prints nothing through `grep` | retry after a minute |
| Spans expire ([How long can you read a trace back?](part-4/4.4-read-back-without-the-console.md#how-long-can-you-read-a-trace-back)) | save the evidence yourself for anything longer ([4.3](part-4/4.3-the-failed-step.md)) |

## 2.8.0 versus newer releases

`requirements.txt` pins `google-adk[otel-gcp]==2.8.0`. An unpinned `>=2.8.0`
build resolved 2.11.0 on 2026-10-02, which changes three things this tutorial
depends on ([saved output](../verification/stage3-34-request-log-cloudrun.txt)):

| Behavior | 2.8.0 | 2.11.0 |
|---|---|---|
| Bridged log export | `CloudLoggingExporter`, `trace` = `projects/P/traces/ID` | OTLP to `telemetry.googleapis.com/v1/logs`, `trace` = bare 32-hex id, so an exact `trace="projects/…"` filter finds only the request log |
| Log name variable | `GOOGLE_CLOUD_DEFAULT_LOG_NAME` | `GCP_DEFAULT_LOG_NAME`; the old one is ignored and lines land under `adk-otel` |
| `execute_tool` parent | `call_llm` | `invoke_agent` |

The `adk-python` main branch at `b0180620` (2026-09-06, source only) adds no span
names. It strips the `generate_content` span name, drops `thought_signature` bytes
from the request and response attributes, and gives `gen_ai.choice` records an
explicit span context. On 2.8.0 Agent Runtime's schema v2 still emits `call_llm`.

## Verification status

All runs used google-adk 2.8.0, Python 3.13, and Gemini 3.7 Flash on Vertex AI.
Records are in [verification/](../verification/). No run opened the Cloud
console, so every console step is written from Google's docs; the right-hand
column names them.

| Page | Date | Record | What it showed | Console steps not observed |
|---|---|---|---|---|
| 1.1, 1.2 | 2026-09-07 | `stage0-local-probes.txt`, `stage1-console-spans.txt` | seven spans, `execute_tool` under `call_llm`, `force_flush()` sufficient | none |
| 1.3 | 2026-09-07, 2026-10-02 | `stage1-console-spans.txt`, `stage5-tool-response-knob.txt` | `llm_request` ~1,955 chars, then `{}` | none |
| 1.4 | 2026-09-07, 2026-10-02 | `stage0-local-probes.txt`; 2026-10-02 rerun on `jwd-dev-3` | the four failure shapes; the raised turn has five spans and two `LookupError` events, each with the message | none |
| 1.5 | 2026-10-02 | `stage5-15-trace-per-turn.txt` | five turns, five trace ids, one `gen_ai.conversation.id` | none |
| 1.6 | 2026-09-07 | `stage1-console-spans.txt` | `fetch_forecast` 0.695 s of the tool's 0.700 s | none |
| 2.1 | 2026-09-07 | `stage2-21-adk-web-otel.txt` | same tree via v1; `service.name=adk-tracing` | **Details** waterfall |
| 2.2 | 2026-10-03 | `stage2-22-adk-deploy-cloudrun.txt` | `adk deploy cloud_run --otel_to_cloud`: seven-span tree; `cloud_run` resource labels; request log id differs from span id | Trace Explorer filters, waterfall, **Attributes**; Logs Explorer `trace` field |
| 2.3 | 2026-09-07, 2026-10-02 | `stage2-23-own-server.txt`, `review-fixes-2026-10-02-part2.txt` | recorded step (500 with no provider); exported step (400 without resource); a closed-port extra exporter fails while the trace still lands | visible step |
| 2.4 | 2026-09-07, 2026-10-02 | `stage2-24-agent-runtime.txt`, `review-fixes-2026-10-02-part2.txt` | `invoke_workflow` root, `call_llm` present, seven spans once the model location is `global`; content off | the engine's **Traces** tab (same traces by `service.name` filter) |
| 2.5 | 2026-09-07, 2026-10-02 | `stage2-25-sampling.txt`, `review-fixes-2026-10-02-part2.txt` | 11 of 20 kept at 0.5 through the `02` server, each with seven spans in Cloud Trace | none |
| 3.1, 3.3 | 2026-09-07, 2026-10-02 | `stage3-31-33-log-join.txt`, `stage5-31-free-join.txt`, `stage5-33-framework-logs.txt`, `review-fixes-2026-10-02-part3.txt` | events under the two `generate_content` spans; framework INFO and the tool's INFO under their spans; `uvicorn.access` absent from Cloud Logging; controls 2 to 4 and a `concurrent` run hold | **Logs & Events**, **View logs** |
| 3.2 | 2026-09-07, 2026-10-02 | `stage3-32-viewer-gate.txt`, `stage5-32-before.txt` | before: no WARNING in Cloud Logging; after: WARNING `spanId` equals the `execute_tool` span | **Logs & Events** before and after |
| 3.4 | 2026-09-07, 2026-10-02 | `stage3-34-propagation.txt`, `stage3-34-request-log-cloudrun.txt`, `review-fixes-2026-10-02-part3.txt` | header id = returned id; `parentbased_always_on` records nothing under an unsampled parent, `always_on` keeps it; Cloud Run request log joins | **Correlate by** `request_log` |
| 4.1 | 2026-10-02 | `stage4-41-slow-step.txt`, `review-fixes-2026-10-02-part4.txt` | per-name percentiles; model spans rank above the tool; medians | **OpenTelemetry service** filter, **Span duration** chart, **Grouped** tab, **Span name** filter, trace details panel, **Attributes** |
| 4.2 | 2026-10-02 | `stage4-42-one-users-request.txt`, `review-fixes-2026-10-02-part4.txt` | five traces for one conversation id; full prompt on turn five; content-off `{}` | **Add filter**, attribute filter, **Search for trace**, trace details panel, **Find in Trace**, **Inputs/Outputs** |
| 4.3 | 2026-10-02 | `stage4-43-failed-step.txt`, `classified-error-92972bbf….txt` | `error.type` filter finds one trace; WARNING under the span | **Span status** filter, bar color, **Attributes**, **Logs & Events** |
| 4.4 | 2026-10-02 | `stage4-44-read-back.txt`, `review-fixes-2026-10-02-part4.txt` | scripts match the raw v1 response (`list_traces.sh` after a same-day fix) | comparison with the Trace Explorer waterfall |
| 2.6, 3.5, 4.5, 4.6 | none | none | reference pages; 4.5's BigQuery section is source only; 4.6 cites the quotas page, read 2026-10-02 | none |

Two cloud probes settled design questions before any page was written:
`stage0-row10-cloudrun-traceparent.txt` (Cloud Run sends both headers) and
`stage0-row12-trace-api-v1.txt` (v1 reads OTLP-ingested spans).

### Not verified

| Item | Status |
|---|---|
| Every console step in the right-hand column above | written from Google's docs |
| A plain `{"error": ...}` tool's user answer and parent status | not captured |
| Ways B and C ([3.5](part-3/3.5-three-ways-to-stamp.md)) and OTLP backends ([2.6](part-2/2.6-other-backends.md)) | not run |
| The BigQuery plugin's `trace_id` columns ([4.5](part-4/4.5-traces-logs-metrics-rows.md)) | source only |
| Everything on 2.11.0 beyond the three rows above | not run; pinned to 2.8.0 |
| The `adk-python` `main` claims above | source only; never run |
| Free tier and per-span price ([4.6](part-4/4.6-cost-retention-content.md)) | linked, not quoted |

## References

- [Cloud Trace: find and explore traces](https://docs.cloud.google.com/trace/docs/finding-traces): the Trace Explorer, filters, **Search for trace**, **Find in Trace**, generative AI events.
- [Cloud Trace: view trace details](https://docs.cloud.google.com/trace/docs/viewing-details): the trace details panel and **Logs & Events**.
- [Cloud Trace: log integration](https://docs.cloud.google.com/trace/docs/trace-log-integration): how `trace` and `spanId` join a log to a span.
- [Cloud Logging: correlate logs](https://docs.cloud.google.com/logging/docs/view/correlate-logs): **Correlate by** in Logs Explorer.
- [Cloud Trace: trace filters](https://docs.cloud.google.com/trace/docs/trace-filters): the v1 list filter syntax.
- [Cloud Trace: quotas and limits](https://docs.cloud.google.com/trace/docs/quotas): retention, attribute limits, read quota.
- [Cloud Trace: migrate to OTLP endpoints](https://docs.cloud.google.com/trace/docs/migrate-to-otlp-endpoints): the Telemetry API as the write path.
- [Cloud Trace: troubleshooting](https://docs.cloud.google.com/trace/docs/troubleshooting): the visible step and an empty **Logs & Events** tab.
- [Python logging client: automatic trace and span extraction](https://docs.cloud.google.com/python/docs/reference/logging/latest/auto-trace-span-extraction): way B's lookup order and the hand-set override rule.
- [Telemetry IAM roles](https://docs.cloud.google.com/iam/docs/roles-permissions/telemetry): the writer roles in Setup.
- [Agent Platform: tracing](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/tracing): Agent Runtime telemetry settings and truncation.
- [Estimating your bills](https://docs.cloud.google.com/stackdriver/estimating-bills) and [Google Cloud Observability pricing](https://cloud.google.com/products/observability/pricing): spans ingested is the billed unit.
- adk.dev [Cloud Trace integration](https://adk.dev/integrations/cloud-trace/) and [traces](https://adk.dev/observability/traces/): ADK's own setup and span attribute docs.
- [Deploy, manage, and observe ADK on Cloud Run](https://codelabs.developers.google.com/deploy-manage-observe-adk-cloud-run): the codelab; it uses the deprecated `--trace_to_cloud` ([2.1](part-2/2.1-adk-web-otel-to-cloud.md)).

---

[← 4.6 · Cost, retention, and content policy](part-4/4.6-cost-retention-content.md)<br>
[Tutorial index](../TUTORIAL.md)
