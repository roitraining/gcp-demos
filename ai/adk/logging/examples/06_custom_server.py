"""Example 06: a streamlined custom ADK server, where you own the logging.

Use case
--------
You are not using ``adk web`` or ``adk api_server`` or ``get_fast_api_app``.
You want a small hand-written FastAPI service around an ADK Runner, following
ADK 2.x best practices, and you want full control of the logging configuration.

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
  ``google_adk`` group.
* A ``TruncateFilter`` caps the noisy model request/response lines so a busy
  server stays readable. This is the "tame framework noise" technique.
* Note ``get_fast_api_app`` has no ``log_level`` argument either, so in any
  custom server the logging config is yours to set up. Do it explicitly.

Run it
------
    .venv/bin/python examples/06_custom_server.py
    # in another terminal:
    curl -s -X POST localhost:8080/chat -H 'content-type: application/json' \
         -d '{"message": "weather in Tokyo?"}'
"""

from __future__ import annotations

import logging
import logging.config
import os
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

from fastapi import FastAPI
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

_structured = import_module("05_structured_plugin")
StructuredTelemetryPlugin = _structured.StructuredTelemetryPlugin
JsonFormatter = _structured.JsonFormatter


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
    """One place that configures every logger this process cares about."""
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"truncate": {"()": TruncateFilter, "max_length": 200}},
            "formatters": {
                "plain": {
                    "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
                },
                "json": {"()": JsonFormatter},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "plain",
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
                # Your structured telemetry logger, on the JSON handler.
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


app = FastAPI(title="Streamlined ADK server", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "web-user"


@app.post("/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    runner: Runner = app.state.runner
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
    return JSONResponse({"response": final})


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    # log_config=None: we already configured logging via dictConfig above, so
    # we do not want uvicorn to install its own config on top of ours.
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
