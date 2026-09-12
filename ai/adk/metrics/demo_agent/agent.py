"""The shared agent for every metrics example in this folder.

It is the logging tutorial's weather agent with one tool added. Two tools of
different latency are the whole reason the tool and token distributions have any
shape:

  - ``get_weather(city)`` is instant and has a success/error branch. The error
    branch (an unknown city) returns a failure ``status`` without raising, which
    is enough for ADK to stamp ``error.type`` on the tool-duration metric.
  - ``get_forecast(city, days)`` sleeps 0.3-1.5 s and returns more text, so it
    lands in slower latency buckets and spends more tokens.

The agent is deliberately boring. The point of this folder is the metrics, not
the agent.
"""

from __future__ import annotations

import random
import time
from typing import Any, Optional

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.adk.tools.function_tool import FunctionTool

from .outcome import outcome_callbacks

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
    # A failure status, not an exception. On its own this does NOT stamp
    # error.type: ADK only reads the response for an error when the tool defines
    # a _detect_error_in_response hook (see StatusAwareTool below). The
    # invocation itself still succeeds either way.
    return {
        "status": "error",
        "error_message": f"No weather data for {city!r}.",
    }


def get_forecast(city: str, days: int = 3) -> dict:
    """Return a multi-day forecast for a city.

    This tool is intentionally slow (a 0.3-1.5 s sleep) and returns more text
    than ``get_weather``, so its latency and token cost sit in different
    histogram buckets.

    Args:
      city: The city to look up.
      days: How many days to forecast, 1-7.

    Returns:
      A dict with a ``status`` and either a ``report`` or an ``error_message``.
    """
    key = city.strip().lower()
    time.sleep(random.uniform(0.3, 1.5))
    if key not in _CITY_WEATHER:
        return {
            "status": "error",
            "error_message": f"No forecast data for {city!r}.",
        }
    days = max(1, min(int(days), 7))
    base = _CITY_WEATHER[key]
    lines = [f"Day {n}: {base}." for n in range(1, days + 1)]
    return {
        "status": "ok",
        "report": f"{days}-day forecast for {city}: " + " ".join(lines),
    }


class StatusAwareTool(FunctionTool):
    """A FunctionTool that reports its own failures to telemetry.

    A plain function tool never stamps ``error.type`` on the tool-duration
    metric for a returned failure status; ADK only reads the response through
    the optional ``_detect_error_in_response`` hook, which ``FunctionTool``
    leaves returning ``None``. Overriding it maps a ``{"status": "error"}``
    result to an ``error.type`` value, so the unknown-city turn produces a
    second attribute set while the invocation still succeeds. Tutorial 1.3
    teaches exactly this.
    """

    def _detect_error_in_response(self, response: Any) -> Optional[str]:
        if isinstance(response, dict) and response.get("status") == "error":
            return "lookup_failed"
        return None


root_agent = Agent(
    name="weather_agent",
    # Pin the model client to the global endpoint. gemini-3.7-flash is served
    # only on `global`, but Agent Engine must deploy to a region (us-central1),
    # and GOOGLE_CLOUD_LOCATION sets both the runtime region and the model
    # endpoint. client_kwargs overrides just the model client's location, so the
    # regional deploy still reaches the global-only model (see 2.5).
    model=Gemini(model="gemini-3.7-flash", client_kwargs={"location": "global"}),
    description="Answers weather and forecast questions for a few known cities.",
    instruction=(
        "You are a concise weather assistant. For a current-weather question,"
        " call get_weather. For a multi-day forecast, call get_forecast. Report"
        " the tool result in one or two sentences. If a tool returns an error,"
        " say you do not have data for that city."
    ),
    tools=[StatusAwareTool(get_weather), StatusAwareTool(get_forecast)],
    # The one custom instrument (page 3.7). Empty unless TUTORIAL_OUTCOME_METRIC
    # is set, so Parts 1-2 emit only the six framework metrics.
    after_tool_callback=outcome_callbacks(),
)
