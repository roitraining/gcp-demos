"""Metrics server plus per-event rows in BigQuery (tutorial 4.1).

This is the 03 metrics server with one addition: a
``BigQueryAgentAnalyticsPlugin`` on the App. The metrics keep flowing to Cloud
Monitoring exactly as in 03; the plugin writes one row per lifecycle event
(user message, LLM request/response, tool start/end, invocation start/end, ...)
to a BigQuery table through the Storage Write API. Metrics answer "how much, how
fast, how often, by dimension"; rows answer "which session, which prompt, at
what cost" (Part 4).

The dataset must already exist -- the plugin creates the table and, with
``create_views=True`` (the default), one ``v_<event_type>`` view per event
type, but not the dataset. Make it once::

    bq mk --location=US --dataset "${GOOGLE_CLOUD_PROJECT}:${BQ_ANALYTICS_DATASET_ID}"

The dataset id comes from ``BQ_ANALYTICS_DATASET_ID`` (matches the ADK sample
agent-observability-bq). The table is ``agent_events``.

Run it locally::

    source env.sh
    export BQ_ANALYTICS_DATASET_ID=agent_analytics
    .venv/bin/python examples/04_bq_plugin.py
    # then, in another terminal, fire baseline turns (tutorial 4.1):
    for i in $(seq 10); do
      curl -s -X POST localhost:8080/chat \
        -H 'content-type: application/json' \
        -d '{"message": "What'\''s the weather in London?"}' >/dev/null
    done
    # then count rows by event type:
    bq query --use_legacy_sql=false \
      'SELECT event_type, COUNT(*) c
       FROM `'"${GOOGLE_CLOUD_PROJECT}.${BQ_ANALYTICS_DATASET_ID}"'.agent_events`
       GROUP BY event_type ORDER BY c DESC'

Requires ``GOOGLE_CLOUD_PROJECT``, ``BQ_ANALYTICS_DATASET_ID``,
``google-adk[otel-gcp]``, and ``bigquery-agent-analytics`` with its Storage
Write API deps.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

from fastapi import FastAPI
from opentelemetry.sdk.resources import Resource
from pydantic import BaseModel

from google.adk.apps.app import App
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import types

from demo_agent.agent import root_agent


def install_cloud_metrics(project: str) -> None:
    """Same metric export as 03: build the exporter, register it with a resource."""
    os.environ.setdefault("OTEL_SERVICE_NAME", "adk-metrics-server")
    resource = Resource.create(
        {
            "gcp.project_id": project,
            "service.name": os.environ["OTEL_SERVICE_NAME"],
        }
    )
    hooks = get_gcp_exporters(enable_cloud_metrics=True)
    maybe_set_otel_providers([hooks], otel_resource=resource)
    print(f"Exporting gen_ai.* metrics to Cloud Monitoring in project {project!r}.")


def build_bq_plugin(project: str) -> BigQueryAgentAnalyticsPlugin:
    """The plugin that turns each lifecycle event into a BigQuery row."""
    dataset_id = os.getenv("BQ_ANALYTICS_DATASET_ID")
    if not dataset_id:
        sys.exit("needs BQ_ANALYTICS_DATASET_ID set (the dataset must already exist)")
    plugin = BigQueryAgentAnalyticsPlugin(
        project_id=project,
        dataset_id=dataset_id,
        table_id="agent_events",
    )
    print(
        f"Writing agent_events rows to {project}.{dataset_id}.agent_events"
        " via the Storage Write API."
    )
    return plugin


@asynccontextmanager
async def lifespan(app: FastAPI):
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        sys.exit("needs GOOGLE_CLOUD_PROJECT set (in .env or the environment)")
    install_cloud_metrics(project)
    app.state.runner = Runner(
        app=App(
            name="metrics_bq_server",
            root_agent=root_agent,
            plugins=[build_bq_plugin(project)],
        ),
        session_service=InMemorySessionService(),
    )
    try:
        yield
    finally:
        await app.state.runner.close()


app = FastAPI(title="Metrics + BigQuery ADK server", lifespan=lifespan)


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
