"""Example 07: Cloud Run-ready structured JSON logs with trace correlation.

Use case
--------
You are deploying the custom server (example 06) to Cloud Run. On Cloud Run,
anything a container writes to stdout/stderr is ingested by Cloud Logging
automatically, and if each line is a JSON object with the right special fields,
Cloud Logging parses it into a structured entry: ``severity`` drives the log
level, and ``logging.googleapis.com/trace`` ties the line to the request's
trace so all logs for one request group together in the Logs Explorer.

Two Cloud Run facts this example encodes
----------------------------------------
* Severity: a plain line on stderr is shown as ERROR regardless of content
  (ADK itself works around this for LiteLLM). Emitting ``severity`` explicitly
  in JSON on stdout avoids the guesswork.
* Trace: Cloud Run sets the ``X-Cloud-Trace-Context`` header (and forwards W3C
  ``traceparent``). Formatting it as
  ``projects/PROJECT_ID/traces/TRACE_ID`` in the special trace field links the
  log line to the request trace.

Run it
------
    GOOGLE_CLOUD_PROJECT=your-project .venv/bin/python examples/07_cloudrun_json.py
    curl -s -X POST localhost:8082/chat \
      -H 'content-type: application/json' \
      -H 'X-Cloud-Trace-Context: 105445aa7843bc8bf206b12000100000/1;o=1' \
      -d '{"message":"weather in San Francisco?"}'
    # every JSON log line for that request carries the same trace value.
"""

from __future__ import annotations

import contextvars
import json
import logging
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

from importlib import import_module

StructuredTelemetryPlugin = import_module("05_structured_plugin").StructuredTelemetryPlugin

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# A context variable holds the current request's trace id so every log record
# emitted while handling that request can pick it up, no matter how deep in the
# call stack (including inside the ADK plugin callbacks).
current_trace: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_trace", default=None
)


class CloudRunJsonFormatter(logging.Formatter):
    """Format records as the JSON structure Cloud Logging understands."""

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


def configure_logging() -> None:
    handler = logging.StreamHandler()  # stdout by default
    handler.setFormatter(CloudRunJsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # Keep ADK framework logs but let them flow through the JSON handler too.
    logging.getLogger("google_adk").setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger("agent.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    adk_app = App(
        name="cloudrun_server",
        root_agent=root_agent,
        plugins=[StructuredTelemetryPlugin()],
    )
    app.state.runner = Runner(app=adk_app, session_service=InMemorySessionService())
    logger.info("runner ready")
    try:
        yield
    finally:
        await app.state.runner.close()


app = FastAPI(title="Cloud Run JSON logging demo", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "web-user"


@app.post("/chat")
async def chat(req: ChatRequest, request: Request) -> JSONResponse:
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

    port = int(os.getenv("PORT", "8082"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
