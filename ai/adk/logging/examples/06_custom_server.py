"""Example 06: a custom ADK server, Cloud Run-ready, where you own the logging.

Use case
--------
You are not using ``adk web`` or ``adk api_server`` or ``get_fast_api_app``.
You want a small hand-written FastAPI service around an ADK Runner, following
ADK 2.x best practices, and you want full control of the logging configuration,
so the exact server you run on your laptop is the one you ship to Cloud Run.

ADK 2.x best practices shown here
---------------------------------
* Build an ``App(name=..., root_agent=..., plugins=[...])`` and pass it to
  ``Runner(app=..., session_service=...)``. The docstring in ``runners.py`` says
  providing ``app`` is the recommended way; passing ``plugins=`` to Runner is
  deprecated.
* Create the Runner once at startup and close it on shutdown, via a FastAPI
  ``lifespan``. ``await runner.close()`` releases toolset/plugin resources.
* Stream with ``runner.run_async(...)``.

Logging control shown here
--------------------------
* A ``dictConfig`` is the clean way to configure everything in one place:
  the root handler, your own ``agent.telemetry`` logger (JSON), and the
  ``google_adk`` group. Every stream lands on the same Cloud Run-ready JSON
  formatter, so each line becomes a structured Cloud Logging entry.
* ``CloudRunJsonFormatter`` writes the two special fields Cloud Logging reads:
  ``severity`` (so the level is what you logged, not a guess Cloud Run makes
  from the stream) and ``logging.googleapis.com/trace`` (so every line of one
  request groups together in the Logs Explorer).
* A ``contextvars.ContextVar`` holds the current request's trace id. The
  formatter reads it for *every* record emitted while the request is handled,
  including the deep ``google_adk`` framework logs you never touch.
* A ``TruncateFilter`` caps the noisy model request/response lines so a busy
  server stays readable. This is the "tame framework noise" technique.

Run it
------
    GOOGLE_CLOUD_PROJECT=your-project .venv/bin/python examples/06_custom_server.py
    # in another terminal, passing the trace header the way Cloud Run would:
    curl -s -X POST localhost:8080/chat \
         -H 'content-type: application/json' \
         -H 'X-Cloud-Trace-Context: 105445aa7843bc8bf206b12000100000/1;o=1' \
         -d '{"message": "weather in Tokyo?"}'
    # every JSON log line for that request carries the same trace value.
"""

from __future__ import annotations

import contextvars
import json
import logging
import logging.config
import os
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from demo_agent.agent import root_agent

# Import the structured plugin from example 05 so this server emits the same
# per-request telemetry. (Both files live in examples/, already on sys.path.)
from importlib import import_module

StructuredTelemetryPlugin = import_module("05_structured_plugin").StructuredTelemetryPlugin

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# A context variable holds the current request's trace id so every log record
# emitted while handling that request can pick it up, no matter how deep in the
# call stack (including inside the ADK plugin callbacks and the google_adk
# framework loggers).
current_trace: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_trace", default=None
)


class CloudRunJsonFormatter(logging.Formatter):
    """Format records as the JSON structure Cloud Logging understands.

    ``severity`` drives the Cloud Logging level; ``logging.googleapis.com/trace``
    ties the line to the request trace so all logs for one request group
    together. Any ``extra={...}`` fields ride along as top-level keys.
    """

    _RESERVED = set(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "severity": record.levelname,  # DEBUG/INFO/WARNING/ERROR -> Cloud Logging severity
            "message": record.getMessage(),
            "logging.googleapis.com/sourceLocation": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            },
        }
        trace_id = current_trace.get()
        if trace_id and PROJECT_ID:
            entry["logging.googleapis.com/trace"] = (
                f"projects/{PROJECT_ID}/traces/{trace_id}"
            )
        for key, value in record.__dict__.items():
            if key not in self._RESERVED:
                entry[key] = value
        return json.dumps(entry, default=str)


def parse_trace_id(request: Request) -> str | None:
    """Extract the trace id from Cloud Run's headers."""
    # Cloud Run / GCLB: "TRACE_ID/SPAN_ID;o=TRACE_TRUE"
    cloud_header = request.headers.get("X-Cloud-Trace-Context")
    if cloud_header:
        return cloud_header.split("/")[0]
    # W3C traceparent: "version-traceid-spanid-flags"
    traceparent = request.headers.get("traceparent")
    if traceparent:
        parts = traceparent.split("-")
        if len(parts) >= 2:
            return parts[1]
    return None


class TruncateFilter(logging.Filter):
    """Cap very long framework log lines so the server log stays readable."""

    def __init__(self, max_length: int = 200) -> None:
        super().__init__()
        self.max_length = max_length

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        if len(msg) > self.max_length:
            record.msg = msg[: self.max_length] + " ...[truncated]"
            record.args = ()
        return True


def configure_logging() -> None:
    """One place that configures every logger this process cares about.

    Every handler uses the Cloud Run JSON formatter, so whether the line comes
    from your code, the plugin, or google_adk, it lands as a structured entry
    with the severity you set and the request's trace id attached.
    """
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"truncate": {"()": TruncateFilter, "max_length": 200}},
            "formatters": {"json": {"()": CloudRunJsonFormatter}},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["truncate"],
                },
                "telemetry": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                },
            },
            "loggers": {
                # The ADK framework group. INFO here; flip to DEBUG to see prompts.
                "google_adk": {"level": "INFO", "handlers": ["console"], "propagate": False},
                # Your structured telemetry logger, on its own handler.
                "agent.telemetry": {
                    "level": "INFO",
                    "handlers": ["telemetry"],
                    "propagate": False,
                },
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )


configure_logging()
logger = logging.getLogger("agent.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the App + Runner once, at startup.
    adk_app = App(
        name="custom_server",
        root_agent=root_agent,
        plugins=[StructuredTelemetryPlugin()],
    )
    app.state.runner = Runner(
        app=adk_app,
        session_service=InMemorySessionService(),
    )
    logger.info("runner ready")
    try:
        yield
    finally:
        # Release plugin/toolset resources on shutdown.
        await app.state.runner.close()
        logger.info("runner closed")


app = FastAPI(title="Cloud Run-ready ADK server", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "web-user"


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> JSONResponse:
    # Set the trace id for this request; every record emitted below (yours, the
    # plugin's, and google_adk's) picks it up in the formatter.
    token = current_trace.set(parse_trace_id(request))
    try:
        runner: Runner = app.state.runner
        logger.info("chat_request_received", extra={"user_id": req.user_id})
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id=req.user_id
        )
        message = types.Content(role="user", parts=[types.Part(text=req.message)])
        final = ""
        async for event in runner.run_async(
            user_id=req.user_id, session_id=session.id, new_message=message
        ):
            if event.is_final_response() and event.content:
                final = event.content.parts[0].text
        logger.info("chat_request_completed", extra={"user_id": req.user_id})
        return JSONResponse({"response": final})
    finally:
        current_trace.reset(token)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    # log_config=None: we already configured logging via dictConfig above, so
    # we do not want uvicorn to install its own config on top of ours.
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
