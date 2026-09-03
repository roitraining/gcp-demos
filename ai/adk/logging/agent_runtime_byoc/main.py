"""Minimal custom-container server for Agent Runtime (tutorial 1.7).

This is the smallest server that Agent Runtime will actually drive. Agent
Runtime does not serve arbitrary routes as its query path: a custom container
must implement two endpoints on port 8080 (the runtime contract):

    POST /api/reasoning_engine          unary   {"class_method","input"} -> {"output"}
    POST /api/stream_reasoning_engine   stream  same body -> newline-delimited JSON

Both just dispatch the named method on an ``AdkApp`` wrapping our agent. That is
the whole server. The logging plumbing is the naive Part 1 config (a level plus
``basicConfig``), identical to example 09, so the point of 1.7 holds: watch the
same unstructured Part 1 logs (yours, ``google_adk``, and the tool line) land in
Cloud Logging under ``reasoning_engine_stdout`` when the platform, not you, runs
the container.

Level comes from ``LOG_LEVEL`` (default ``info``), set on the deployment's env.
"""

from __future__ import annotations

import inspect
import json
import logging
import os

# Agent Runtime injects GOOGLE_CLOUD_LOCATION = the deploy region (us-central1)
# and will not let us override it at deploy time (it is a reserved env var). But
# gemini-3.7-flash is served from `global`, not us-central1, so the model lookup
# 404s unless we point the genai client at the model's location. MODEL_LOCATION
# is our own (non-reserved) var; apply it before importing the agent, which is
# what initializes the genai client.
if os.getenv("MODEL_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.environ["MODEL_LOCATION"]

from fastapi import FastAPI, Request, responses

from demo_agent.agent import root_agent


def configure(level_name: str) -> None:
    """The example 01 / example 09 logging config: a level, plain text."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s - %(name)s - %(message)s")
    logging.getLogger().setLevel(level)
    logging.getLogger("google_adk").setLevel(level)


configure(os.getenv("LOG_LEVEL", "info"))
logger = logging.getLogger("agent.server")

# AdkApp wraps the ADK agent and exposes the reasoning-engine class methods
# (create_session, stream_query, async_stream_query, ...) the platform calls.
from vertexai import agent_engines  # noqa: E402  (import after logging setup)

adk_app = agent_engines.AdkApp(agent=root_agent)

app = FastAPI(title="Agent Runtime BYOC (naive Part 1 logging)")


async def _invoke(method, input_val: dict):
    """Call an AdkApp method with kwargs, awaiting if needed."""
    result = method(**input_val)
    if inspect.isawaitable(result):
        result = await result
    return result


@app.post("/api/reasoning_engine")
async def reasoning_engine(request: Request) -> responses.JSONResponse:
    body = await request.json()
    method = getattr(adk_app, body["class_method"])
    output = await _invoke(method, body.get("input") or {})
    return responses.JSONResponse({"output": output})


@app.post("/api/stream_reasoning_engine")
async def stream_reasoning_engine(request: Request) -> responses.StreamingResponse:
    body = await request.json()
    method = getattr(adk_app, body["class_method"])
    input_val = body.get("input") or {}

    async def gen():
        # stream_query / async_stream_query yield events; forward each as a line.
        result = method(**input_val)
        if inspect.isasyncgen(result):
            async for chunk in result:
                yield json.dumps(chunk, default=str) + "\n"
        elif inspect.isgenerator(result):
            for chunk in result:
                yield json.dumps(chunk, default=str) + "\n"
        else:
            if inspect.isawaitable(result):
                result_val = await result
            else:
                result_val = result
            yield json.dumps({"output": result_val}, default=str) + "\n"

    return responses.StreamingResponse(gen(), media_type="application/json")


if __name__ == "__main__":
    import uvicorn

    # Agent Runtime requires the container to listen on 8080.
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
