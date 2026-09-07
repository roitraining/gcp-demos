"""Your own server, with one trace per request (tutorial 3.4).

03_correlated_server.py stamps your logs with ADK's trace id -- but ADK opens a
fresh trace per request and ignores the inbound trace header, so on Cloud Run the
request log and ADK's spans still carry two different trace ids.

This server closes that gap. It adds, on top of 03:

  - FastAPIInstrumentor.instrument_app(app): a server span that extracts the
    inbound trace context, so ADK's root becomes a CHILD of the request instead
    of a new root. Now one request is one trace.
  - a composite propagator (W3C traceparent + GCP X-Cloud-Trace-Context), so both
    header formats are understood. On Cloud Run the W3C header alone would do, but
    the composite also handles GCP-only callers.
  - OTEL_TRACES_SAMPLER=always_on, set BEFORE the provider is built, to defeat the
    sampling trap: a propagated unsampled parent (traceparent flags 00) would
    otherwise make ParentBased drop every ADK span. See 3.4's deep dive.

Run it locally::

    source env.sh
    .venv/bin/python examples/04_propagated_server.py
    # then (3.4), tag the request and check the returned id equals the header's:
    curl -s -X POST localhost:8080/chat -H 'content-type: application/json' \
      -H 'traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01' \
      -d '{"text":"What'\''s the weather in London?"}'
"""

from __future__ import annotations

import contextvars
import logging
import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

# Set the sampler BEFORE the provider is built (install_* below reads it via the
# SDK). always_on defeats the unsampled-parent trap once propagation is on.
os.environ.setdefault("OTEL_TRACES_SAMPLER", "always_on")

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry._logs import get_logger_provider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.sdk._logs import LoggingHandler
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from pydantic import BaseModel

try:
    from opentelemetry.propagators.cloud_trace_propagator import (
        CloudTraceFormatPropagator,
    )
except ImportError:  # opentelemetry-propagator-gcp not installed
    CloudTraceFormatPropagator = None

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
    def export(self, spans) -> SpanExportResult:
        for s in spans:
            # With a server span present, ADK's root has a parent; the outermost
            # span is the FastAPI server span. Capture whichever span has no
            # parent -- the true root of the request's trace.
            if s.parent is None:
                try:
                    _current_trace.set(format(s.context.trace_id, "032x"))
                except Exception:
                    pass
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass


def install() -> None:
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    os.environ.setdefault("OTEL_SERVICE_NAME", "adk-trace-server")

    # The composite propagator: understand both header formats.
    propagators = [TraceContextTextMapPropagator()]
    if CloudTraceFormatPropagator is not None:
        propagators.append(CloudTraceFormatPropagator())
    set_global_textmap(CompositePropagator(propagators))

    hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)
    if not isinstance(hooks, OTelHooks):
        hooks = OTelHooks(span_processors=list(hooks))
    hooks.span_processors.append(BatchSpanProcessor(_TraceIdCapture()))
    maybe_set_otel_providers([hooks], otel_resource=get_gcp_resource(project))

    handler = LoggingHandler(level=logging.INFO, logger_provider=get_logger_provider())
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    print(
        f"Exporting spans and bridged logs to Cloud in project {project!r};"
        f" one trace per request (sampler={os.environ['OTEL_TRACES_SAMPLER']})."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    install()
    app.state.runner = Runner(
        app=App(name="trace_server", root_agent=root_agent),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        trace.get_tracer_provider().force_flush()
        await app.state.runner.close()


app = FastAPI(title="Propagated tracing ADK server", lifespan=lifespan)
# Add the server span and extract the inbound trace context on every request.
FastAPIInstrumentor.instrument_app(app)


class ChatRequest(BaseModel):
    text: str


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    runner: Runner = app.state.runner
    _current_trace.set("")
    logger.info("chat request received")
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
    # The request's trace id is the current span's, now that a server span exists.
    tid = format(trace.get_current_span().get_span_context().trace_id, "032x")
    return {"response": final, "trace_id": tid}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
