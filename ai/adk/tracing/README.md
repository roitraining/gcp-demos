# ADK agent tracing

A hands-on tour of the traces an ADK agent emits, how to ship them to Cloud
Trace, how to get every log line of a request to show up inside the right span,
and how to use traces to answer the questions an on-call engineer asks. Part 1
runs entirely on your laptop against a real model; the cloud parts (2 to 4) ship
the same tree to Google Cloud and read it back.

The one idea that makes the rest simple: **a trace is the tree of spans ADK
opens around one turn; its trace id is the key every log line can carry; and
Cloud Trace draws the logs inside the spans when both carry the same id in the
same project.** Generate, collect, correlate, consume, in that order.

Start with **[TUTORIAL.md](TUTORIAL.md)**.

> Verified against google-adk 2.8.0 (pinned) on Python 3.13, serving Gemini 3.7
> Flash via Vertex AI. Part 1 is captured from real local runs (2026-09-07);
> Parts 2 to 4 from live Cloud Trace and Cloud Logging (2026-09-07 to
> 2026-10-02).

## Files

| Path | What it is |
|---|---|
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, the trace-tree idea, and the table of contents. Start here. |
| [tutorial/](tutorial/) | The tutorial itself: Setup, Scenarios, then one short page per numbered subtask, grouped into `part-N/` folders. |
| [tutorial/scenarios.md](tutorial/scenarios.md) | The controlled experiments every page runs. |
| [tutorial/how-to-choose.md](tutorial/how-to-choose.md) | The reference page: span and attribute catalog, correlation decision table, verification status. |
| [demo_agent/agent.py](demo_agent/agent.py) | The shared agent: `get_weather` (instant, with an error branch) and `get_forecast` (slow, with a helper the custom span wraps), plus three tutorial gates. |
| [examples/01_console_spans.py](examples/01_console_spans.py) | One turn, a console span exporter that writes `out/spans.json`, a flush: the raw span tree (1.2, 1.4, 1.6). |
| [examples/02_trace_server.py](examples/02_trace_server.py) | A hand-written server that exports the tree to Cloud Trace and returns each turn's trace id (2.3). |
| [examples/03_correlated_server.py](examples/03_correlated_server.py) | `02` plus a logging bridge, so your log lines land under their spans (3.2, 3.3, Part 4). |
| [examples/04_propagated_server.py](examples/04_propagated_server.py) | `03` plus inbound trace-context propagation and an always-on sampler: one trace per request (3.4). |
| [examples/_common.py](examples/_common.py) | Shared bootstrap, the console-span exporter, the flush helper, and the run loop. |
| [trace/](trace/) | The Trace v1 read-back scripts (`get_trace.sh`, `list_traces.sh`) every cloud capture uses (4.4 explains them). |
| [load/turns.sh](load/turns.sh) | Fires N turns of a named scenario at a running server; the load tool from Part 2 on. |
| [deploy/Dockerfile.trace_server](deploy/Dockerfile.trace_server) | Container for the `02` server on Cloud Run (2.2); `SERVER` selects `03` or `04`. |
| [requirements.txt](requirements.txt) | `google-adk[otel-gcp]==2.8.0` (pinned) plus the OTLP, Cloud Logging, FastAPI-instrumentation, and propagator packages. |
| [verification/](verification/) | Run records behind the captured output on each page. |

## Quick start

Create the environment and install dependencies:

```bash
cd ai/adk/tracing
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Copy the templates, then edit `.env` for your project and model config and
`env.sh` to set `PROJECT_ID` (the shell variables the cloud parts read):

```bash
cp .env.example .env
cp env.sh.example env.sh
```

Run the first example, then read the tutorial:

```bash
.venv/bin/python examples/01_console_spans.py
```

## Status

Parts 1 to 4 are written and their output captured from real runs (Part 1
locally on 2026-09-07; Parts 2 to 4 against live Cloud Trace and Cloud Logging,
2026-09-07 to 2026-10-02). Part 4's console clicks are written as instructions
and not yet observed. The reference page and the final link check are in
progress. The plan and its verification tables live in
`docs/adk-trace-tutorial.md` in the repo root.
