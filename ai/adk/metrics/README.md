# ADK agent metrics

A hands-on tour of the metrics an ADK agent emits, how to ship them to Cloud
Monitoring, how to read them as operational signals, and when to reach past
metrics to per-event rows in BigQuery. Part 1 runs entirely on your laptop
against a real model; the cloud parts (2 to 4) are drafted, with their live
Cloud Monitoring and BigQuery captures still to be run.

The one idea that makes the rest simple: a metric is **a number recorded into a
histogram at one of three moments (a model call, a tool call, or an agent
invocation ending), tagged with a few attributes, and aggregated in the process
before you see it.** The tutorial builds that model step by step.

Start with **[TUTORIAL.md](TUTORIAL.md)**.

> Verified against google-adk 2.8.0 on Python 3.13, serving Gemini 3.7 Flash via
> Vertex AI. Part 1 is captured from real runs; Parts 2 to 4 are drafted with
> `NEEDS-RUN` markers where a live cloud capture is still owed.

## Files

| Path | What it is |
|---|---|
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, the three-moments idea, and the table of contents. Start here. |
| [tutorial/](tutorial/) | The tutorial itself: Setup, Scenarios, then one short page per numbered subtask, grouped into `part-N/` folders. |
| [tutorial/scenarios.md](tutorial/scenarios.md) | The controlled experiments every page runs. The spine of the tutorial. |
| [demo_agent/agent.py](demo_agent/agent.py) | The shared agent: `get_weather` (instant, with an error branch) and `get_forecast` (slow), wrapped in a `StatusAwareTool`. |
| [examples/01_console_metrics.py](examples/01_console_metrics.py) | One turn, a metric reader that writes `out/metrics.json`, a flush: your first datapoint (1.1). |
| [examples/03_histogram_shape.py](examples/03_histogram_shape.py) | Ten turns, then draw a token histogram from its own buckets (1.2). |
| [examples/02_two_attribute_sets.py](examples/02_two_attribute_sets.py) | London then Atlantis; one metric splits into two attribute sets (1.3). |
| [examples/05_workflow_metrics.py](examples/05_workflow_metrics.py) | A two-agent `SequentialAgent`; agent-grain metrics split by name (1.5). |
| [examples/03_metrics_server.py](examples/03_metrics_server.py) | A hand-written server that exports `gen_ai.*` to Cloud Monitoring (2.4). |
| [examples/04_bq_plugin.py](examples/04_bq_plugin.py) | The server plus `BigQueryAgentAnalyticsPlugin`, one row per event (Part 4). |
| [examples/_common.py](examples/_common.py) | Shared bootstrap, reader helpers, histogram rendering, and the run loop. |
| [load/turns.sh](load/turns.sh) | Fires N turns of a named scenario at a running server; the load tool from Part 2 on. |
| [queries/](queries/) | The PromQL and Cloud Monitoring config the Part 3 pages paste. |
| [deploy/](deploy/) | Dockerfile and env files for Cloud Run and Agent Runtime (2.3, 2.5). |

## Quick start

Create the environment and install dependencies:

```bash
cd ai/adk/metrics
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
.venv/bin/python examples/01_console_metrics.py
```

## Status

Part 1 (pages 1.1–1.5) and its example scripts are verified end to end against a
real GCP project (2026-09-06). Setup, Scenarios, and the index are written. Parts
2 to 4 (collect, consume, BigQuery), the reference page, and all runnable assets
(`load/turns.sh`, the server and plugin examples, `queries/`, `deploy/`) are
drafted; every cloud read-back block is marked `NEEDS-RUN` until captured against
live Cloud Monitoring and BigQuery. The plan and its verification tables live in
`docs/adk-metrics-tutorial.md` in the repo root.
