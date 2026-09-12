"""The shared agent for every tracing example in this folder.

It is the logging tutorial's weather agent with a forecast tool added and three
tutorial gates. The gates let one agent show every span shape the tutorial
teaches without editing code between pages; unset, the span tree is pure ADK.

  - ``get_weather(city)`` is instant, with a success branch and an error branch.
    Unknown city returns a failure ``status`` and logs a WARNING. That failure is
    invisible to the trace by default: a plain ``FunctionTool`` stamps no
    ``error.type`` on ``execute_tool`` for a returned status.
  - ``get_forecast(city, days)`` calls ``_fetch_forecast()``, which sleeps
    0.3-1.5 s and logs one INFO line. The sleep gives the tool span real
    duration; the helper is a separate function so a custom span (page 1.6) can
    wrap it *inside* the tool body.

Three env gates, each defaulting off (see the Scope table in the plan):

  - ``TUTORIAL_CUSTOM_SPAN=1``   -> ``_fetch_forecast`` runs inside a
    ``fetch_forecast`` span, a child of ``execute_tool`` (page 1.6).
  - ``TUTORIAL_CLASSIFY_ERRORS=1`` -> both tools are wrapped in
    ``StatusAwareTool``, whose ``_detect_error_in_response`` maps a failure
    status to ``error.type="lookup_failed"`` and turns the tool span red (1.4).
  - ``TUTORIAL_RAISE_ON_UNKNOWN=1`` -> ``get_weather`` raises ``LookupError`` for
    an unknown city instead of returning a status, so the exception propagates and
    both parent spans go ERROR (1.4 deep dive).

The agent is deliberately boring. The point of this folder is the spans.
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Any, Optional

from google.adk.agents import Agent
from google.adk.tools.function_tool import FunctionTool
from opentelemetry import trace

logger = logging.getLogger("demo_agent")

# A tracer on our own scope. get_tracer resolves against whatever TracerProvider
# is installed -- ADK's, once a reader/exporter is set up -- so a span opened
# here nests under ADK's spans by the SDK's implicit context.
tracer = trace.get_tracer(__name__)

# A hardcoded lookup so the agent runs without any external dependency.
_CITY_WEATHER = {
    "san francisco": "18C and foggy",
    "new york": "24C and clear",
    "london": "15C and drizzling",
    "tokyo": "27C and humid",
}


def get_weather(city: str) -> dict:
    """Return the current weather for a city.

    Args:
      city: The city to look up, for example "London".

    Returns:
      A dict with a ``status`` and either a ``report`` or an ``error_message``.
    """
    key = city.strip().lower()
    if key in _CITY_WEATHER:
        return {
            "status": "ok",
            "report": f"The weather in {city} is {_CITY_WEATHER[key]}.",
        }
    # Unknown city. Under TUTORIAL_RAISE_ON_UNKNOWN the tool raises, so the
    # exception propagates through execute_tool and both parents (1.4 deep dive).
    # Otherwise it returns a failure status and logs a WARNING -- the only
    # failure evidence, and it is outside the trace until Part 3 bridges it.
    if os.getenv("TUTORIAL_RAISE_ON_UNKNOWN"):
        raise LookupError(f"No weather data for {city!r}.")
    logger.warning("weather lookup failed for %r: no data", city)
    return {
        "status": "error",
        "error_message": f"No weather data for {city!r}.",
    }


def _fetch_forecast(city: str, days: int) -> str:
    """The slow part of get_forecast: sleep, log one line, build the report.

    Kept separate from get_forecast so page 1.6 can wrap this call in a custom
    span without the wrapper leaking into the tool's public signature.
    """
    time.sleep(random.uniform(0.3, 1.5))
    logger.info("fetched %d-day forecast for %s", days, city)
    base = _CITY_WEATHER[city.strip().lower()]
    lines = [f"Day {n}: {base}." for n in range(1, days + 1)]
    return f"{days}-day forecast for {city}: " + " ".join(lines)


def get_forecast(city: str, days: int = 3) -> dict:
    """Return a multi-day forecast for a city.

    This tool is intentionally slow (a 0.3-1.5 s sleep in ``_fetch_forecast``)
    so its span owns most of ``invoke_agent``'s duration. With
    ``TUTORIAL_CUSTOM_SPAN`` set, the sleep runs inside a ``fetch_forecast``
    child span carrying a ``forecast.days`` attribute (page 1.6).

    Args:
      city: The city to look up.
      days: How many days to forecast, 1-7.

    Returns:
      A dict with a ``status`` and either a ``report`` or an ``error_message``.
    """
    key = city.strip().lower()
    if key not in _CITY_WEATHER:
        logger.warning("forecast lookup failed for %r: no data", city)
        return {
            "status": "error",
            "error_message": f"No forecast data for {city!r}.",
        }
    days = max(1, min(int(days), 7))
    if os.getenv("TUTORIAL_CUSTOM_SPAN"):
        with tracer.start_as_current_span("fetch_forecast") as span:
            span.set_attribute("forecast.days", days)
            report = _fetch_forecast(city, days)
    else:
        report = _fetch_forecast(city, days)
    return {"status": "ok", "report": report}


class StatusAwareTool(FunctionTool):
    """A FunctionTool that reports its own failures to telemetry.

    A plain function tool never stamps ``error.type`` on the ``execute_tool``
    span for a returned failure status; ADK only reads the response through the
    optional ``_detect_error_in_response`` hook, which ``FunctionTool`` leaves
    returning ``None`` for a status dict. Overriding it maps a
    ``{"status": "error"}`` result to an ``error.type``, so the failing tool span
    goes red while the invocation still succeeds. Page 1.4 teaches exactly this.
    """

    def _detect_error_in_response(self, response: Any) -> Optional[str]:
        if isinstance(response, dict) and response.get("status") == "error":
            return "lookup_failed"
        return None


# TUTORIAL_CLASSIFY_ERRORS picks the tool wrapper. Unset: plain FunctionTool, so
# a returned error status leaves the span UNSET (1.4, plain). Set: StatusAwareTool,
# so the same status turns the span red with error.type=lookup_failed (1.4,
# classified).
_ToolClass = (
    StatusAwareTool if os.getenv("TUTORIAL_CLASSIFY_ERRORS") else FunctionTool
)

root_agent = Agent(
    name="weather_agent",
    model="gemini-3.7-flash",
    description="Answers weather and forecast questions for a few known cities.",
    instruction=(
        "You are a concise weather assistant. For a current-weather question,"
        " call get_weather. For a multi-day forecast, call get_forecast. Report"
        " the tool result in one or two sentences. If a tool returns an error,"
        " say you do not have data for that city."
    ),
    tools=[_ToolClass(get_weather), _ToolClass(get_forecast)],
)
