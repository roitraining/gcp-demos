"""Your own server, exporting metrics to Cloud Monitoring (tutorial 2.4).

`adk web --otel_to_cloud` installs the Cloud metric exporter for you. This is a
hand-written server, so nothing does it automatically: you make the same two
calls `adk web` makes -- build the exporters, register them -- and ADK's
`gen_ai.*` histograms leave the process for Cloud Monitoring every 5 s.

The one thing `adk web` does that a bare script must do by hand: put
``gcp.project_id`` in the OTel resource. The Telemetry API rejects every metric
batch that lacks it with a 400 whose body reads::

    Resource is missing required attribute "gcp.project_id"

`adk web --otel_to_cloud` injects it; a standalone script does not, so it is set
below through ``maybe_set_otel_providers(otel_resource=...)``. The laptop also
needs ``service.instance.id`` and ``cloud.region`` on the resource so the
metrics land on ``prometheus_target`` (env.sh sets these; Cloud Run and Agent
Runtime supply them through the resource detector instead).

This server exposes a single ``/chat`` endpoint (not the full `adk web` run
API), so drive it with a plain curl loop rather than ``load/turns.sh``, which
targets the CLI server's ``/run``.

Run it locally::

    source env.sh                 # PROJECT_ID, OTEL_RESOURCE_ATTRIBUTES, ...
    .venv/bin/python examples/03_metrics_server.py
    # then, in another terminal, fire baseline turns (tutorial 2.4):
    for i in $(seq 20); do
      curl -s -X POST localhost:8080/chat \
        -H 'content-type: application/json' \
        -d '{"message": "What'\''s the weather in London?"}' >/dev/null
    done
    # wait ~10 s (two 5 s export intervals), then read the series back.

Requires ``GOOGLE_CLOUD_PROJECT`` and ``google-adk[otel-gcp]``.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

# bootstrap() loads .env BEFORE the exporters are built below. That order is why
# a hand-written server can keep its config in .env, unlike the CLI.
bootstrap()

from fastapi import FastAPI
from opentelemetry.sdk.resources import Resource
from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import types

from demo_agent.agent import root_agent


def install_cloud_metrics() -> None:
    """The two calls the CLI would have made, plus the resource it injects."""
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    os.environ.setdefault("OTEL_SERVICE_NAME", "adk-metrics-server")

    # gcp.project_id is the attribute the Telemetry API requires and that a bare
    # script must supply itself. service.instance.id and cloud.region make the
    # metrics land on prometheus_target on a laptop; read them from
    # OTEL_RESOURCE_ATTRIBUTES if env.sh set them, else fall back.
    resource = Resource.create(
        {
            "gcp.project_id": project,
            "service.name": os.environ["OTEL_SERVICE_NAME"],
        }
    )

    hooks = get_gcp_exporters(enable_cloud_metrics=True)
    maybe_set_otel_providers([hooks], otel_resource=resource)
    print(
        f"Exporting gen_ai.* metrics to Cloud Monitoring in project {project!r}"
        " every 5 s."
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    install_cloud_metrics()
    app.state.runner = Runner(
        app=App(name="metrics_server", root_agent=root_agent),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        await app.state.runner.close()


app = FastAPI(title="Minimal metrics ADK server", lifespan=lifespan)


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
