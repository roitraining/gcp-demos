[← 4.5 · Cost, retention, and content policy](part-4/4.5-cost-retention-content.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# How to choose & reference

*The span catalog, the failure and correlation decisions, and the version caveats. The last page.*

> [!NOTE]
> **Why you are here.** This page is a reference, not a lesson. Use it to look up
> a span or attribute, pick a correlation setup, and check what changes after
> google-adk 2.8.0.

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
[4.5 · Cost, retention, and content policy](part-4/4.5-cost-retention-content.md#what-should-never-be-in-a-span).
With both defaults, the only prompt text Cloud Trace holds is on the spans.
Whether the **Inputs/Outputs** tab renders it is not verified.

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

[← 4.5 · Cost, retention, and content policy](part-4/4.5-cost-retention-content.md)<br>
[Tutorial index](../TUTORIAL.md)
