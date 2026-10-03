"""Your own server, exporting the span tree to Cloud Trace (tutorial 2.3).

`adk web --otel_to_cloud` installs the Cloud trace exporter for you. This is a
hand-written server, so nothing does it automatically: you make the same two
calls `adk web` makes -- build the exporters, register them with the resource --
and ADK's span tree leaves the process for Cloud Trace over OTLP.

Two things the CLI does that a bare script must do by hand:

  - Pass the GCP resource. `get_gcp_exporters` builds exporters only; the CLI
    separately builds ``get_gcp_resource(project_id)`` and hands it to
    ``maybe_set_otel_providers(otel_resource=...)``. Left out, the provider falls
    back to ``OTELResourceDetector().detect()``, which carries no
    ``gcp.project_id`` (see 2.3's "exported" step).
  - Return the trace id. So the caller can read its own request back, ``/chat``
    returns the invocation's ``trace_id``. A tiny span processor records each
    session's trace id as its spans end.

``TUTORIAL_TRACE_ENDPOINT`` adds a second OTLP span exporter aimed at that URL,
beside the Google one (2.3's ``export-outage``: a closed port, so that extra
export fails and retries). The Google export is unaffected, so the trace still
reaches Cloud Trace.

Run it locally::

    source env.sh
    .venv/bin/python examples/02_trace_server.py
    # then drive it (2.3):
    HOST=http://localhost:8080 ENDPOINT=chat ./load/turns.sh baseline 1
    # each line prints the trace id; read it back with trace/get_trace.sh
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

# bootstrap() loads .env BEFORE the exporters are built. That order is why a
# hand-written server can keep its config in .env, unlike the CLI.
bootstrap()

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import SpanProcessor
from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters, get_gcp_resource
from google.adk.telemetry.setup import OTelHooks, maybe_set_otel_providers
from google.genai import types

from demo_agent.agent import root_agent

# Session id -> trace id, filled by the span processor below as each turn's
# spans end, so /chat can return the id of the trace it just produced.
_trace_by_session: dict[str, str] = {}


class _TraceIdCapture(SpanProcessor):
    """Records each session's trace id when a span carrying it ends.

    ``invoke_agent`` carries ``gen_ai.conversation.id`` (the session id). on_end
    runs synchronously as the span closes, so the id is in the map before
    ``run_async`` returns. Runs alongside the real Cloud exporter.
    """

    def on_end(self, span) -> None:
        session_id = (span.attributes or {}).get("gen_ai.conversation.id")
        if session_id:
            _trace_by_session[session_id] = format(span.context.trace_id, "032x")


def install_cloud_tracing() -> None:
    """The calls the CLI would have made, plus the resource it injects."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    os.environ.setdefault("OTEL_SERVICE_NAME", "adk-trace-server")

    # TUTORIAL_TRACE_ENDPOINT adds a second OTLP span exporter (2.3 export-outage).
    # It is a standard OTel var, so ADK's setup adds a generic OTLP exporter for it
    # beside the Google one; it does not replace the Google exporter.
    endpoint = os.getenv("TUTORIAL_TRACE_ENDPOINT")
    if endpoint:
        os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = endpoint
        print(f"(extra span exporter sending to {endpoint})")

    hooks = get_gcp_exporters(enable_cloud_tracing=True, enable_cloud_logging=True)
    if not isinstance(hooks, OTelHooks):
        hooks = OTelHooks(span_processors=list(hooks))
    # Add the trace-id capture next to the Cloud exporter.
    hooks.span_processors.append(_TraceIdCapture())

    maybe_set_otel_providers([hooks], otel_resource=get_gcp_resource(project))
    print(f"Exporting spans to Cloud Trace in project {project!r}.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_cloud_tracing()
    app.state.runner = Runner(
        app=App(name="trace_server", root_agent=root_agent),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        trace.get_tracer_provider().force_flush()
        await app.state.runner.close()


app = FastAPI(title="Minimal tracing ADK server", lifespan=lifespan)


class ChatRequest(BaseModel):
    text: str


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    runner: Runner = app.state.runner
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
    # Flush so this turn's spans leave for Cloud Trace now, not on the next batch.
    trace.get_tracer_provider().force_flush()
    return {"response": final, "trace_id": _trace_by_session.pop(session.id, "")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
