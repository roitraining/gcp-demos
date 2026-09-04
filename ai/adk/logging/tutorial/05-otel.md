# Part 5 · OpenTelemetry

*Stream 4 — GenAI spans to Cloud Trace, and the content-capture privacy knob.*

> [!NOTE]
> **Why you are here.** Everything so far was the `logging` module (streams 1-3).
> Stream 4 is separate machinery: ADK emits **OpenTelemetry** spans, one per LLM
> call and tool call, plus GenAI events. They never print; they leave through an
> exporter. You want them because a span tree tells you *where the latency went* in
> a way flat log lines cannot. This is what `adk web --otel_to_cloud` turns on, and
> you can drive it yourself.

**👉 Do this** in console mode, which needs no cloud access and just prints the
spans.

**Command:**

```bash
.venv/bin/python examples/08_otel_cloud.py
```

**Expected output** — the span hierarchy:

```console
"name": "invocation"
  "name": "invoke_agent weather_agent"
    "name": "call_llm"
      "name": "generate_content gemini-3.7-flash"
    "name": "execute_tool get_weather"
    "name": "call_llm"
```

> [!IMPORTANT]
> **What it means.** This is the same run you have watched all tutorial, now shown
> as nested timed spans: the whole invocation contains the agent, which makes a
> first model call, executes the tool, then makes a second model call. Exported to
> Cloud Trace, each span carries a duration, so you can see at a glance whether your
> latency is in the model or the tool.

**To export it to Google Cloud**, the setup is two calls:

```python
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers

hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)
maybe_set_otel_providers([hooks])   # note: a LIST of hooks
```

**Command:**

```bash
.venv/bin/python examples/08_otel_cloud.py cloud
```

Spans land in **Cloud Trace**; GenAI events land in **Cloud Logging** under the
log name `adk-otel`. This mode needs two extra packages, already in
`requirements.txt`: `opentelemetry-exporter-otlp-proto-http` and
`opentelemetry-exporter-gcp-logging`.

---

### 7.1 The privacy knob you must know about

By default, this telemetry carries **metadata only**; prompt and response text
are elided. One environment variable controls it, and it must be set **before ADK
is imported**:

```bash
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT   # safe default
# other values that DO include content: SPAN_ONLY | EVENT_ONLY | SPAN_AND_EVENT
```

> [!IMPORTANT]
> **What it means.** Leave it at `NO_CONTENT` in production unless you have a
> specific, reviewed reason to capture prompts and responses, because captured
> content then lives in your logging backend under its retention and access rules.
> For a one-off, scope it through `RunConfig.telemetry` instead of flipping the
> whole process.

> [!NOTE]
> The richest GenAI **content events** ride on ADK's experimental semantic
> conventions, an area the SDK marks as subject to change. The **spans** and the
> setup shown here are stable; treat the exact shape of content events as
> evolving, and pin your `google-adk` version.

---

← Prev: [4. Structured logging](04-production.md) · [Tutorial index](../TUTORIAL.md) · Next: [6. Agent Runtime](06-agent-runtime.md) →

