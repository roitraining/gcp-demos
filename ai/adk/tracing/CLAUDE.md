# ADK tracing tutorial

## Governing model

A trace is the tree of spans ADK opens around one turn. Its trace id is the key
every log line can carry, and Cloud Trace draws the logs inside the spans when
both carry the same id in the same project. Parts 1 to 4 follow generate,
collect, correlate, consume.

## Facts that are easy to get wrong (google-adk 2.8.0)

- The single-tool baseline tree is seven spans with five names:
  `invocation → invoke_agent → {call_llm → [generate_content, execute_tool],
  call_llm → generate_content}`. `execute_tool` parents `call_llm`, not
  `invoke_agent`.
- `error.type` on `execute_tool` depends on the tool:
  - Returning `{"status": "error"}` leaves the span UNSET with no `error.type`.
  - Returning `{"error": ...}` gets `error.type=TOOL_ERROR`.
  - The demo's `StatusAwareTool` hook maps its failure status to
    `error.type=lookup_failed`.
  - Raising gives ERROR with `error.type=<class>`, two exception events on the
    tool span, ERROR on `invoke_agent` and `invocation`, and five spans instead
    of seven. The status description holds the full message.
- Content on spans is on by default. `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false`
  empties it; the log-event content setting has the opposite default (page 1.3).
- Scripts using a `BatchSpanProcessor` call `flush_spans()` from
  `examples/_common.py`.
- The Trace v1 API returns `spanId` as a decimal uint64, and a new trace 404s
  with "Trace bucket not found" for about 90 to 120 s. Retry; don't fail.
- Under the default `ParentBased(ALWAYS_ON)` sampler, an unsampled inbound
  `traceparent` drops every ADK span; `OTEL_TRACES_SAMPLER=always_on` restores
  them (page 3.4).

## Conventions

- Demo-agent gates, each on only when set to `1`: `TUTORIAL_CUSTOM_SPAN` (1.6),
  `TUTORIAL_CLASSIFY_ERRORS` (1.4), `TUTORIAL_RAISE_ON_UNKNOWN` (1.4 deep dive).
- The `02` and `03` servers return the trace id from a span processor keyed on
  `gen_ai.conversation.id`; `04` reads the server span. A sampled-out turn
  returns no id.
- Read traces back with `trace/get_trace.sh <trace-id>`, and logs with
  `gcloud logging read 'trace="projects/P/traces/ID"' --project="$PROJECT_ID"`.
- Prompts: "What's the weather in London?" for single turns, "What's the
  three-day forecast for London?" for the slow tool, and "What's the weather in
  Atlantis?" for errors.
- Captured output comes from `jwd-gcp-demos`, which has a Model Armor floor
  setting that sanitizes every Gemini call. New captures belong on a project
  without one, such as `jwd-dev-5`. Save run records under `verification/`.
