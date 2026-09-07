# ADK agent tracing

A hands-on tour of the traces an ADK agent emits, how to ship them to Cloud
Trace, how to get every log line of a request to show up inside the right span,
and how to use traces to answer the questions an on-call engineer asks. Part 1
runs entirely on your laptop against a real model; the cloud parts (2 to 4) ship
the same tree to Google Cloud and read it back.

The one idea that makes the rest simple: **a trace is the tree of spans ADK
opens around one turn; its trace id is the key every log line can carry; and
Cloud Trace draws the logs inside the spans when both carry the same id in the
same project.** Generate, collect, correlate, consume — in that order.

Start with **[TUTORIAL.md](TUTORIAL.md)**.

> Verified against google-adk 2.8.0 on Python 3.13, serving Gemini 3.7 Flash via
> Vertex AI. Part 1 is captured from real local runs (2026-09-07); the cloud
> parts are drafted, with their live Cloud Trace and Cloud Logging captures
> tracked in the plan.

## Files

| Path | What it is |
|---|---|
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, the trace-tree idea, and the table of contents. Start here. |
| [tutorial/](tutorial/) | The tutorial itself: Setup, Scenarios, then one short page per numbered subtask, grouped into `part-N/` folders. |
| [tutorial/scenarios.md](tutorial/scenarios.md) | The controlled experiments every page runs. The spine of the tutorial. |
| [demo_agent/agent.py](demo_agent/agent.py) | The shared agent: `get_weather` (instant, with an error branch) and `get_forecast` (slow, with a helper the custom span wraps), plus three tutorial gates. |
| [examples/01_console_spans.py](examples/01_console_spans.py) | One turn, a console span exporter that writes `out/spans.json`, a flush: the raw span tree (1.2, 1.4, 1.6). |
| [examples/_common.py](examples/_common.py) | Shared bootstrap, the console-span reader, the flush helper, and the run loop. |
| [trace/](trace/) | The Trace v1 read-back scripts (`get_trace.sh`, `list_traces.sh`) every cloud capture uses. |
| [load/turns.sh](load/turns.sh) | Fires N turns of a named scenario at a running server; the load tool from Part 2 on. |
| [deploy/](deploy/) | Dockerfile and env files for Cloud Run and Agent Runtime. |

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

Stage 0 (open-question probes) and Stage 1 (scaffold and Part 1) are verified
against a real GCP project (2026-09-07). Setup, Scenarios, the index, and Part 1
pages (1.0–1.6) with their captured span trees are written. Parts 2 to 4
(collect, correlate, consume), the reference page, and the remaining runnable
assets are in progress; every cloud read-back block is captured against live
Cloud Trace and Cloud Logging as its stage runs. The plan and its verification
tables live in `docs/adk-trace-tutorial.md` in the repo root.
