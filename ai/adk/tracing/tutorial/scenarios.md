[← 0 · Setup](00-setup.md)<br>
[→ Part 1 · What a trace is](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)

---

# Scenarios

*The controlled experiments every page runs. One scenario per lesson.*

> [!NOTE]
> **Why you are here.** This is the spine of the tutorial. Each page names one
> scenario from the table below and one question it answers. You run the same
> agent every time and change exactly one condition, so the part of the trace
> that moves is the lesson.

Part 1 runs a scenario as a short script. From Part 2 on, you run it under load
with `load/turns.sh <scenario> [N]`, which fires N turns of the named scenario
against a running server.

## The scenarios

| Scenario | Controlled change | Observation to capture | Operational question |
|---|---|---|---|
| `baseline` | One London turn per fresh session | Five span names in one tree; two `call_llm`, one `execute_tool`, tool ~1 ms | What does one turn look like as a tree? |
| `slow-tool` | Forecast turns, so `get_forecast` sleeps 0.3–1.5 s | `execute_tool get_forecast` owns most of `invoke_agent`; model spans unchanged | Is the dependency responsible for the slowdown? |
| `custom-span` | `slow-tool` with `TUTORIAL_CUSTOM_SPAN=1` | a `fetch_forecast` child under `execute_tool`; the gap inside the tool span now has a name | Where inside my tool did the time go? |
| `returned-error` | Atlantis; plain `FunctionTool`, `get_weather` returns a failure status and logs a WARNING | `execute_tool get_weather` UNSET, no `error.type`, no exception event; `invoke_agent` OK; the model says there is no data. The WARNING is the only failure evidence, outside the trace until 3.2 | Did execution finish without satisfying the request? |
| `classified-error` | Same turn with `TUTORIAL_CLASSIFY_ERRORS=1`: `StatusAwareTool` maps the status to `lookup_failed` | `execute_tool` ERROR, `error.type=lookup_failed`, no exception event; parents OK; same answer; the WARNING sits under the red span once 3.2 is done | Which step failed, and what did it say? |
| `raised-error` | Same turn with `TUTORIAL_RAISE_ON_UNKNOWN=1`: `get_weather` raises `LookupError` | `execute_tool` ERROR, `error.type=LookupError`, two `exception` events; `invoke_agent` and `invocation` ERROR; no answer, the request fails | Where did execution stop, and what evidence survived? |
| `multi-turn` | Five turns in one session | five traces sharing one `gen_ai.conversation.id`; input tokens climb per `call_llm` | How do I see a whole conversation? |
| `tagged-request` | `curl` with a `traceparent` (sampled) or `X-Cloud-Trace-Context` header | before 3.4: two trace ids for one request; after: one | Is this trace the one my user's request produced? |
| `unsampled-parent` | `curl` with `traceparent` flags `00` against 04 | with the default sampler: no spans; with always-on: the full tree | Why did propagation make my traces disappear? |
| `content-off` | `ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false` | `llm_request`, `llm_response`, `tool_call_args` read `{}`; the **Inputs/Outputs** tab empties | Can I trace without storing prompts? |
| `export-outage` | `TUTORIAL_TRACE_ENDPOINT` at a closed port, one London turn against `02`; then unset, restart, one more turn | the outage turn answers; the exporter logs a failed export; the read-back finds nothing for it; the restored turn's tree lands | Can the agent answer while traces are missing, and which rung failed? |
| `concurrent` | `turns.sh concurrent 4`: forecast and London turns fired in parallel, each from its own session | disjoint trace ids; every bridged log line carries the span of its own request; no line under another request's span | Do logs stay attached to the right request under overlap? |

## The agent behind them

All scenarios drive the one shared agent in
[demo_agent/agent.py](../demo_agent/agent.py):

- `get_weather(city)` is instant, with a success branch and an error branch. The
  error branch returns a failure status, logs a WARNING, and does not raise (or
  raises `LookupError`, under `TUTORIAL_RAISE_ON_UNKNOWN`).
- `get_forecast(city, days)` calls `_fetch_forecast()`, which sleeps 0.3–1.5 s
  and logs one INFO line, so its span owns real time. Under `TUTORIAL_CUSTOM_SPAN`
  the sleep runs inside a `fetch_forecast` child span.

Two tools of different latency are the only reason the tree has any shape.

---

[← 0 · Setup](00-setup.md)<br>
[→ Part 1 · What a trace is](part-1/index.md)<br>
[Tutorial index](../TUTORIAL.md)
