"""Example 05: a production plugin that emits real ``logging`` records.

Use case
--------
You want the lifecycle visibility of LoggingPlugin, but as genuine ``logging``
records so your handlers, formatters, and log routing apply. This is the
bridge between "nice terminal output" and "structured logs in Cloud Logging".

What to notice
--------------
* This is a ``BasePlugin`` subclass. The callbacks (``before_model_callback``,
  ``after_model_callback``, ``before_tool_callback``, ``after_tool_callback``,
  ``on_tool_error_callback``) are where you hook in.
* It logs through ``logging.getLogger("agent.telemetry")``, so it obeys whatever
  handler/formatter you configure. Here we attach a tiny JSON formatter to prove
  the point; example 07 reuses this exact idea for Cloud Run.
* It records latency and token usage. ``extra={...}`` fields ride along on the
  record and become structured fields in the JSON output.
* Plugin vs callback: a plugin is app-wide (every agent, every tool). Per-agent
  ``before_tool_callback=`` on a single ``Agent`` is the surgical alternative
  when you only care about one agent or tool.

Run it
------
    .venv/bin/python examples/05_structured_plugin.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Optional

from _common import ask, bootstrap

bootstrap()

from google.adk.agents.callback_context import CallbackContext
from google.adk.apps.app import App
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import InMemoryRunner
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

from demo_agent.agent import root_agent

telemetry_log = logging.getLogger("agent.telemetry")


class StructuredTelemetryPlugin(BasePlugin):
    """Logs model and tool activity as structured ``logging`` records.

    Everything here goes through the ``logging`` module, so it inherits your
    handlers and formatters instead of printing directly like LoggingPlugin.
    """

    def __init__(self, name: str = "structured_telemetry") -> None:
        super().__init__(name=name)
        self._model_started: dict[str, float] = {}
        self._tool_started: dict[str, float] = {}

    async def before_model_callback(
        self, *, callback_context: CallbackContext, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        self._model_started[callback_context.invocation_id] = time.monotonic()
        telemetry_log.info(
            "llm_request",
            extra={"event": "llm_request", "agent": callback_context.agent_name},
        )
        return None  # returning None means "proceed normally"

    async def after_model_callback(
        self, *, callback_context: CallbackContext, llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        started = self._model_started.pop(callback_context.invocation_id, None)
        latency_ms = round((time.monotonic() - started) * 1000, 1) if started else None
        usage = getattr(llm_response, "usage_metadata", None)
        telemetry_log.info(
            "llm_response",
            extra={
                "event": "llm_response",
                "agent": callback_context.agent_name,
                "latency_ms": latency_ms,
                "input_tokens": getattr(usage, "prompt_token_count", None),
                "output_tokens": getattr(usage, "candidates_token_count", None),
            },
        )
        return None

    async def before_tool_callback(
        self, *, tool: BaseTool, tool_args: dict[str, Any], tool_context: ToolContext
    ) -> Optional[dict[str, Any]]:
        self._tool_started[tool_context.function_call_id] = time.monotonic()
        # Note: key names in ``extra`` must not collide with reserved LogRecord
        # attributes (``args``, ``name``, ``message``, ``module``, ...). We use
        # ``tool_args`` rather than ``args`` for exactly that reason.
        telemetry_log.info(
            "tool_start",
            extra={"event": "tool_start", "tool": tool.name, "tool_args": tool_args},
        )
        return None

    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        started = self._tool_started.pop(tool_context.function_call_id, None)
        latency_ms = round((time.monotonic() - started) * 1000, 1) if started else None
        telemetry_log.info(
            "tool_end",
            extra={
                "event": "tool_end",
                "tool": tool.name,
                "latency_ms": latency_ms,
                "status": (result or {}).get("status"),
            },
        )
        return None

    async def on_tool_error_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception,
    ) -> Optional[dict[str, Any]]:
        telemetry_log.error(
            "tool_error",
            extra={"event": "tool_error", "tool": tool.name, "error": str(error)},
        )
        return None


class JsonFormatter(logging.Formatter):
    """Minimal JSON line formatter. Example 07 extends this for Cloud Run."""

    # Attributes present on every LogRecord; anything else was passed via extra.
    _RESERVED = set(
        logging.makeLogRecord({}).__dict__
    ) | {"message", "asctime"}

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key, value in record.__dict__.items():
            if key not in self._RESERVED:
                payload[key] = value
        return json.dumps(payload, default=str)


async def main() -> None:
    # Route just our telemetry logger through the JSON formatter so the
    # structured fields are visible. (ADK's own google_adk.* logs are left
    # on the root handler; example 06 shows how to tune those too.)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    telemetry_log.addHandler(handler)
    telemetry_log.setLevel(logging.INFO)
    telemetry_log.propagate = False  # don't double-log through the root handler

    app = App(
        name="structured_demo",
        root_agent=root_agent,
        plugins=[StructuredTelemetryPlugin()],
    )
    runner = InMemoryRunner(app=app)

    answer = await ask(runner, "What's the weather in New York?")
    print("\nFINAL ANSWER:", answer)

    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
