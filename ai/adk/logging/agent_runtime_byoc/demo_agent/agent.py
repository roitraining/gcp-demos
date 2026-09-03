"""A tiny shared agent used by every logging example in this folder.

It has exactly one tool. The tool deliberately emits a log record of its own,
using a plain module logger, so you can watch *your* application logs sit
alongside the framework's ``google_adk.*`` logs in every example.

The agent is intentionally boring. The point of this folder is the logging,
not the agent, so nothing here should distract from that.
"""

from __future__ import annotations

import logging
import os

from google.adk.agents import Agent

# A normal module-level logger. This is NOT under the ``google_adk`` tree, so
# it is a stand-in for the logging your own tools and business code produce.
logger = logging.getLogger(__name__)

# Tutorial 1.6 (Agent Runtime): on a native agent deploy there is no server
# script of ours to set the log level, so the agent module reads it from the
# LOG_LEVEL env var. This runs ONLY when LOG_LEVEL is set, so the local examples
# (01-08), which configure their own logging, are unaffected. basicConfig is a
# no-op if the runtime already installed a root handler, so we also setLevel
# explicitly, which applies either way.
if os.getenv("LOG_LEVEL"):
    _level = getattr(logging, os.environ["LOG_LEVEL"].upper(), logging.INFO)
    logging.basicConfig(level=_level, format="%(levelname)s - %(name)s - %(message)s")
    logging.getLogger().setLevel(_level)
    logging.getLogger("google_adk").setLevel(_level)

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
      city: The city to look up, for example "San Francisco".

    Returns:
      A dict with a ``status`` and either a ``report`` or an ``error_message``.
    """
    key = city.strip().lower()
    logger.info("tool get_weather called for city=%r", city)
    if key in _CITY_WEATHER:
        return {"status": "ok", "report": f"The weather in {city} is {_CITY_WEATHER[key]}."}
    logger.warning("tool get_weather has no data for city=%r", city)
    return {
        "status": "error",
        "error_message": f"No weather data for {city!r}.",
    }


# The model id is read here so every example shares one definition. Gemini 3.7
# Flash is cheap and fast, which suits repeated tutorial runs.
root_agent = Agent(
    name="weather_agent",
    model="gemini-3.7-flash",
    description="Answers questions about the weather in a few known cities.",
    instruction=(
        "You are a concise weather assistant. When the user asks about weather,"
        " call the get_weather tool and report its result in one sentence. If the"
        " tool returns an error, say you do not have data for that city."
    ),
    tools=[get_weather],
)
