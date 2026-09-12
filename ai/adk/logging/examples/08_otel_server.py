"""Example 08: a minimal ADK server that exports OTel GenAI events to Cloud Logging.

When `adk web` / `adk api_server` start your process they install the OpenTelemetry
Cloud exporters for you. This is a hand-written server (like `06_custom_server.py`),
so nothing installs them — you make the two calls below and the `gen_ai.*` events
leave the process for Cloud Logging.

The content knob is set through the environment:
``OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`` — ``NO_CONTENT`` (default)
logs metadata only; ``EVENT_ONLY`` includes prompt/response text. ADK reads it
per turn, so on your own server it can live in ``.env`` (loaded before the
exporters here) locally, or in ``--set-env-vars`` on Cloud Run.

Run it locally::

    .venv/bin/python examples/08_otel_server.py
    # then, in another terminal:
    curl -s -X POST localhost:8080/chat \
         -H 'content-type: application/json' \
         -d '{"message": "What is the weather in London?"}'

Requires ``GOOGLE_CLOUD_PROJECT`` and ``opentelemetry-exporter-gcp-logging``.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

# bootstrap() loads .env BEFORE we build the exporters below. That order is why a
# hand-written server can keep every OTEL_* var in .env, unlike the CLI (5.2).
bootstrap()

from fastapi import FastAPI
from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import types

from demo_agent.agent import root_agent


def install_cloud_logging() -> None:
    """The two calls the CLI would have made: build the exporter, register it."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    os.environ.setdefault("OTEL_SERVICE_NAME", "weather-agent")

    # Project and credentials come from ADC; the Cloud Logging exporter needs no
    # OTel resource.
    hooks = get_gcp_exporters(enable_cloud_logging=True)
    maybe_set_otel_providers([hooks])
    print(f"Exporting gen_ai.* events to Cloud Logging in project {project!r}.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_cloud_logging()
    app.state.runner = Runner(
        app=App(name="otel_server", root_agent=root_agent),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        await app.state.runner.close()


app = FastAPI(title="Minimal OTel ADK server", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(req: ChatRequest) -> dict[str, str]:
    runner: Runner = app.state.runner
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="u1"
    )
    message = types.Content(role="user", parts=[types.Part(text=req.message)])
    final = ""
    async for event in runner.run_async(
        user_id="u1", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content:
            final = event.content.parts[0].text
    return {"response": final}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
