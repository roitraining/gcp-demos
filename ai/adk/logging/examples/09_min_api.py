"""Example 09: the naive Part 1 logging, put behind a real HTTP server.

Use case
--------
Part 1 ran the agent from a plain script (01) and from ADK's own servers
(``adk web``, ``adk api_server``). This is the third way: a tiny hand-written
FastAPI server that does *nothing* clever about logging. It configures logging
exactly the way 01 does, a level plus ``logging.basicConfig``, and it leaves
uvicorn on its default log config, so the bare ``INFO:`` access lines from 1.3
show up unchanged.

The point is to deploy this to Cloud Run (tutorial 1.5) and see the raw,
unstructured Part 1 logs land in Cloud Logging: your ``demo_agent.agent`` line,
the ``google_adk`` framework lines, and uvicorn's access lines, all as plain
text, none of them structured. That is the "before" picture. Part 5 onward is
the "after".

Contrast with examples 06/07: those own the logging config with a ``dictConfig``
and a JSON formatter, and pass ``log_config=None`` to uvicorn. This one does
neither, on purpose.

Level comes from the ``LOG_LEVEL`` env var (default ``info``), the server's
equivalent of 01's command-line argument. On Cloud Run, set it with
``--update-env-vars LOG_LEVEL=warning`` and redeploy to change the dial.

Run it
------
    LOG_LEVEL=info .venv/bin/python examples/09_min_api.py
    # in another terminal:
    curl -s -X POST localhost:8083/chat -H 'content-type: application/json' \
         -d '{"message": "What'\''s the weather in Tokyo?"}'
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from _common import bootstrap

bootstrap()

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from google.adk.runners import InMemoryRunner
from google.genai import types

from demo_agent.agent import root_agent


def configure(level_name: str) -> None:
    """Exactly what example 01 does: a level on the root and google_adk loggers.

    ``basicConfig`` installs a plain-text stderr handler *if the root has none
    yet*; the explicit ``setLevel`` calls apply the level regardless of who
    installed the handler, which matters in a hosted runtime that may configure
    logging before this module imports.
    """
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s - %(name)s - %(message)s")
    logging.getLogger().setLevel(level)
    logging.getLogger("google_adk").setLevel(level)


configure(os.getenv("LOG_LEVEL", "info"))
logger = logging.getLogger("agent.server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.runner = InMemoryRunner(agent=root_agent, app_name="min_api")
    logger.info("runner ready")
    try:
        yield
    finally:
        await app.state.runner.close()


app = FastAPI(title="Minimal ADK server (naive Part 1 logging)", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "web-user"


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "healthy"}


@app.post("/chat")
async def chat(req: ChatRequest) -> JSONResponse:
    runner: InMemoryRunner = app.state.runner
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

    port = int(os.getenv("PORT", "8083"))
    # No log_config here, on purpose: uvicorn installs its own default config,
    # so the bare "INFO:" access lines appear exactly as in tutorial 1.3.
    uvicorn.run(app, host="0.0.0.0", port=port)
