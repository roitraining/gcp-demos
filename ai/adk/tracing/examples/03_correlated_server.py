"""Your own server, with your log lines correlated to the spans (tutorial 3.2).

02_trace_server.py exports the tree, but only ADK's own gen_ai.* events land in
the trace. Your logger.info, the framework's log lines, uvicorn's -- none of them
carry the trace id, so none show up under a span.

This server adds one thing: a bridge from the stdlib logging root to the OTel
logs pipeline (way A). An OTel LoggingHandler captures the ambient span on every
record, and the CloudLoggingExporter that get_gcp_exporters already installed
writes the record's trace_id/span_id as the LogEntry's trace/spanId. So a
log line emitted inside a tool lands under that tool's execute_tool span.

At startup it logs one line OUTSIDE any span -- 3.3's first negative control:
that line gets no trace field, because there is no current span when it runs.

Run it locally::

    source env.sh
    .venv/bin/python examples/03_correlated_server.py
    # then (3.2), a classified-error turn so the failing span is red:
    export TUTORIAL_CLASSIFY_ERRORS=1
    HOST=http://localhost:8080 ENDPOINT=chat ./load/turns.sh returned-error 1
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry._logs import get_logger_provider
from opentelemetry.sdk._logs import LoggingHandler
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
import contextvars

from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers
from google.genai import types

from demo_agent.agent import root_agent

_current_trace: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_trace", default=""
)
logger = logging.getLogger("trace_server")


class _TraceIdCapture(SpanExporter):
    """Records the root span's trace id into a ContextVar so /chat can return it."""

    def export(self, spans) -> SpanExportResult:
        for s in spans:
            if s.parent is None:
                try:
                    _current_trace.set(format(s.context.trace_id, "032x"))
                except Exception:
                    pass
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def install_cloud_tracing_and_logging() -> None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    os.environ.setdefault("OTEL_SERVICE_NAME", "adk-trace-server")

    hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)
    if not isinstance(hooks, OTelHooks):
        hooks = OTelHooks(span_processors=list(hooks))
    hooks.span_processors.append(BatchSpanProcessor(_TraceIdCapture()))
    maybe_set_otel_providers([hooks], otel_resource=get_gcp_resource(project))

    # Way A: bridge the stdlib root logger to the OTel logs pipeline. The handler
    # stamps each record with the current span; the CloudLoggingExporter (already
    # installed by enable_cloud_logging) writes trace/spanId from it.
    handler = LoggingHandler(level=logging.INFO, logger_provider=get_logger_provider())
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    print(f"Exporting spans and bridged logs to Cloud in project {project!r}.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_cloud_tracing_and_logging()
    # 3.3's first negative control: a line logged outside any span. It gets no
    # trace field, so nothing lists it under a span.
    logger.info("trace server starting up (no span here)")
    app.state.runner = Runner(
        app=App(name="trace_server", root_agent=root_agent),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        trace.get_tracer_provider().force_flush()
        await app.state.runner.close()


app = FastAPI(title="Correlated tracing ADK server", lifespan=lifespan)


class ChatRequest(BaseModel):
    text: str


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    runner: Runner = app.state.runner
    _current_trace.set("")
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="u1"
    )
    message = types.Content(role="user", parts=[types.Part(text=req.text)])
    final = ""
    async for event in runner.run_async(
        user_id="u1", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content:
            final = event.content.parts[0].text
    trace.get_tracer_provider().force_flush()
    get_logger_provider().force_flush()
    return {"response": final, "trace_id": _current_trace.get()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
