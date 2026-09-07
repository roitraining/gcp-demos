# ADK tracing tutorial — conventions

Scope: the tutorial under `ai/adk/tracing/`. Applies when editing the tutorial
docs, examples, or deploy scripts here.

Page anatomy, nav, code-block labels, callouts, deep dives, and voice follow the
`tutorial-style` skill in `.claude/skills/tutorial-style/`. Load it first. This
file holds only what is specific to this tutorial. The full plan, decisions, and
verification tables live in `docs/adk-trace-tutorial.md` at the repo root.

## Layout

- `TUTORIAL.md` is the index. `tutorial/00-setup.md` is page 0.
  `tutorial/scenarios.md` is the scenario spine, linked from the index and every
  part landing page. `tutorial/part-N/index.md` is each part's landing page;
  subtask pages are `tutorial/part-N/N.M-slug.md`.
- The linear thread runs index → 00-setup → scenarios → part-1/index → 1.1 … →
  part-2/index → … → how-to-choose.
- Links to shared assets (`examples/`, `demo_agent/`, `trace/`, `load/`,
  `deploy/`) are `../../` from a `part-N/` page, but `../` from `00-setup.md`,
  `scenarios.md`, and `how-to-choose.md`, which sit at `tutorial/` root.

## The governing model

The whole tutorial rests on one idea: **a trace is the tree of spans ADK opens
around one turn; its trace id is the key every log line can carry; and Cloud
Trace draws the logs inside the spans when both carry the same id in the same
project.** Generate → collect → correlate → consume, in that order (Parts 1–4).
Keep new content consistent with this framing.

## Verified facts specific to this build (google-adk 2.8.0)

- **The single-tool baseline tree is seven spans, five names.**
  `invocation → invoke_agent → {call_llm → [generate_content, execute_tool],
  call_llm → generate_content}`.
- **`execute_tool` parents `call_llm`, not `invoke_agent`.** ADK opens the tool
  span while still inside the `call_llm` that emitted the function call. Verified
  Stage 0 on both the console exporter and the Trace v1 read-back. (The plan's
  first draft drew it under `invoke_agent`; that was wrong.)
- **`error.type` on `execute_tool` is conditional (three cases).** A plain
  `FunctionTool` returning `{"status": "error"}` leaves the span UNSET with no
  `error.type`. A returned `{"error": ...}` dict gets `error.type=TOOL_ERROR`
  for free. The demo's `{"status": "error"}` shape needs the `StatusAwareTool`
  hook to become `error.type=lookup_failed`. A raising tool gets ERROR,
  `error.type=<class>`, **two** exception events on the tool span
  (`LookupError` + a `DynamicNodeFailError` wrapper), and ERROR on both parents.
  See page 1.4.
- **Script export needs a flush.** A `BatchSpanProcessor` holds spans until its
  interval, so example scripts call `force_flush()` on the tracer provider
  (helper `flush_spans()` in `examples/_common.py`). `SimpleSpanProcessor`
  (used by the console examples) exports on span end and does not strictly need
  it, but the call is harmless.
- **Content on spans is on by default.** `gcp.vertex.agent.llm_request` holds
  the full prompt; `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` turns
  `llm_request`, `llm_response`, and `tool_call_args` into `"{}"`. This is the
  opposite default from `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`,
  which governs the log events (page 1.3).
- **The Trace v1 API reads OTLP-ingested spans**, so `trace/get_trace.sh` uses
  it. Two gotchas: `spanId` comes back as a **decimal uint64** (not hex), and
  there is a **~90–120 s** ingestion delay whose 404 says
  "_Trace bucket not found_" — retry, don't fail.
- **Cloud Run sends both `traceparent` and `X-Cloud-Trace-Context`** (same trace
  id) and preserves an inbound `traceparent`, so the W3C propagator alone
  suffices for the external path; the composite is only for GCP-only callers.
- **The sampling trap.** Under the default `ParentBased(ALWAYS_ON)`, an unsampled
  remote parent (`traceparent` flags `00`) drops every ADK span;
  `OTEL_TRACES_SAMPLER=always_on` restores the full tree. Page 3.4's deep dive.

## Examples

- Local examples live in `examples/NN_name.py`; the shared agent is
  `demo_agent/`, shared helpers are `examples/_common.py`.
- Every console block on a page is captured from a real run against
  `jwd-gcp-demos`. Token counts and durations vary run to run (a real model), so
  quote them as representative, not exact. Save the run record under
  `verification/`.
- `install_console_spans()` writes its JSON to a file (default `out/spans.json`)
  rather than the console, since a full span dump is too long to read in a
  terminal; pages tell the reader to open it. The `out/` folder is gitignored.

## Demo-agent gates

The one agent shows every span shape through env gates, all default off so the
tree is pure ADK:

- `TUTORIAL_CUSTOM_SPAN=1` — a `fetch_forecast` span inside the forecast tool (1.6).
- `TUTORIAL_CLASSIFY_ERRORS=1` — wrap tools in `StatusAwareTool`, so a returned
  failure status turns the tool span red (1.4).
- `TUTORIAL_RAISE_ON_UNKNOWN=1` — `get_weather` raises `LookupError` for an
  unknown city (1.4 deep dive).

## Tutorial-specific conventions

- The repeated prompts: "What's the weather in London?" for single turns;
  "What's the three-day forecast for London?" for the slow tool; "What's the
  weather in Atlantis?" for the error turns; `load/turns.sh <scenario> [N]` for
  volume.
- Cloud captures use `trace/get_trace.sh <trace-id>` (Trace v1, indented tree)
  and `gcloud logging read 'trace="projects/P/traces/ID"'` for the log side.
