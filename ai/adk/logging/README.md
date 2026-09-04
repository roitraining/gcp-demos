# ADK agent logging

A hands-on tour of logging strategies for ADK agents, across every way you serve
them (`adk web`, `adk api_server`, a hand-written server) and both places you
deploy them (Cloud Run, Vertex AI Agent Engine). Every example runs locally
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
| [TUTORIAL.md](TUTORIAL.md) | The tutorial index: intro, the four-streams idea, setup, and the table of contents. Start here. |
| [tutorial/](tutorial/) | The tutorial itself, one short file per part (log levels, plugins, Cloud Run, and so on). |
| [demo_agent/agent.py](demo_agent/agent.py) | The tiny shared agent (a weather tool that logs). |
| [examples/01_log_levels.py](examples/01_log_levels.py) | Run one prompt at DEBUG/INFO/WARNING/ERROR and compare. |
| [examples/02_tame_uvicorn.py](examples/02_tame_uvicorn.py) | Configure uvicorn logging; drop health-check access spam. |
| [examples/03_logging_plugin.py](examples/03_logging_plugin.py) | Built-in `LoggingPlugin` for live terminal narration. |
| [examples/04_debug_plugin.py](examples/04_debug_plugin.py) | `DebugLoggingPlugin`: full invocation capture to YAML. |
| [examples/05_structured_plugin.py](examples/05_structured_plugin.py) | Custom `BasePlugin` emitting real JSON `logging` records. |
| [examples/06_custom_server.py](examples/06_custom_server.py) | Streamlined ADK 2.x server; you own the `dictConfig`. |
| [examples/07_cloudrun_json.py](examples/07_cloudrun_json.py) | Cloud Run JSON logs with trace correlation. |
| [examples/08_otel_cloud.py](examples/08_otel_cloud.py) | OTel GenAI telemetry to Cloud Trace + Cloud Logging. |
| [deploy/](deploy/) | Dockerfile and deploy scripts for Cloud Run and Agent Engine. |

## Quick start

```bash
cd ai/adk/logging
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then set your project / model config
.venv/bin/python examples/01_log_levels.py debug   # start here, then read the tutorial
```

## Status

The Python examples (02 to 08) are verified end to end against a real GCP
project. The `deploy/` scripts are syntax-checked with flags matching
`adk 2.8.0`, but the deploys themselves are left for you to run. See the
Verification status section in [TUTORIAL.md](TUTORIAL.md) for the precise split.
