# ADK agent logging

A hands-on tour of logging strategies for ADK agents, across every way you serve
them (`adk web`, `adk api_server`, a hand-written server) and both places you
deploy them (Cloud Run, and Agent Runtime with `adk deploy agent_engine`). Every example runs locally
against a real model; the cloud steps are optional.

The one idea that makes the rest simple: an ADK agent process produces **four
log streams** (your code, the `google_adk` framework, the uvicorn web server,
and OpenTelemetry GenAI telemetry). They are configured in different places and
land in different destinations. The tutorial builds that model step by step.

Start with **[TUTORIAL.md](TUTORIAL.md)**.

> Verified against google-adk 2.8.0 on Python 3.13, serving Gemini 3.7 Flash via
> Vertex AI.

## Files

| Path | What it is |
|---|---|
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, the four-streams idea, and the table of contents. Start here. |
| [tutorial/](tutorial/) | The tutorial itself: a Setup page, then one short page per numbered subtask, grouped into `part-N/` folders (log levels, plugins, Cloud Run, and so on). |
| [demo_agent/agent.py](demo_agent/agent.py) | The tiny shared agent (a weather tool that logs). |
| [examples/01_log_levels.py](examples/01_log_levels.py) | Run one prompt at DEBUG/INFO/WARNING/ERROR and compare. |
| [examples/02_tame_uvicorn.py](examples/02_tame_uvicorn.py) | Configure uvicorn logging; drop health-check access spam. |
| [examples/03_logging_plugin.py](examples/03_logging_plugin.py) | Built-in `LoggingPlugin` for live terminal narration. |
| [examples/04_debug_plugin.py](examples/04_debug_plugin.py) | `DebugLoggingPlugin`: full invocation capture to YAML. |
| [examples/05_structured_plugin.py](examples/05_structured_plugin.py) | Custom `BasePlugin` emitting real JSON `logging` records. |
| [examples/06_custom_server.py](examples/06_custom_server.py) | Cloud Run-ready ADK 2.x server where you write the logging config yourself, so every line carries a `severity` and its request's trace id. |
| [examples/08_otel_server.py](examples/08_otel_server.py) | Minimal ADK server that installs the OTel exporter and sends `gen_ai.*` events to Cloud Logging. |
| [examples/09_min_api.py](examples/09_min_api.py) | A bare FastAPI server with naive logging, deployed in 1.5. |
| [otel/](otel/) | `check_local.sh`, which asserts the span names a plain `adk web` produces (5.1). |
| [agent_runtime_byoc/](agent_runtime_byoc/) | The custom container and deploy scripts for Agent Runtime BYOC (1.7). |
| [deploy/](deploy/) | Dockerfiles and deploy scripts for Cloud Run and Agent Runtime. |

## Quick start

```bash
cd ai/adk/logging
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
cp env.sh.example env.sh
```

Then set your project in `.env` and `PROJECT_ID` in `env.sh`, and run the first
example:

```bash
source env.sh
.venv/bin/python examples/01_log_levels.py debug
```

## Status

The Python examples (01–06, 08, 09) are verified against a real GCP project,
except the items under Not verified in
[How to choose & reference](tutorial/how-to-choose.md). See its Verification
status section for what ran and when.
