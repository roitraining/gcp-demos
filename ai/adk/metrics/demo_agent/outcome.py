"""The one custom instrument in the whole tutorial (page 3.7).

Every framework metric answers "how much, how fast, how often". None of them
can answer "did the user actually get weather?" -- a turn whose tool failed
still completes, so ``invoke_agent.duration`` records no error. This module adds
a single counter that closes that gap:

  - ``tutorial.weather.requests`` with one attribute, ``outcome``, taken from
    the tool's returned ``status``: ``answered`` when the lookup succeeded,
    ``unavailable`` when it returned an error status. Nothing is parsed from
    model text; the mapping is the allowlist below.

It is recorded in an ``after_tool_callback`` and attached to the agent ONLY when
``TUTORIAL_OUTCOME_METRIC`` is set, so every earlier page shows exactly the six
framework metrics. The meter is ``metrics.get_meter("tutorial.weather")``, which
resolves against whatever MeterProvider is installed -- the one
``adk web --otel_to_cloud`` sets up, so the counter rides the same export path
to Cloud Monitoring and arrives as ``.../tutorial.weather.requests/counter``.

To turn it on::

    export TUTORIAL_OUTCOME_METRIC=1
    adk web --otel_to_cloud
"""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import metrics

# The full allowlist of outcomes, printed on page 3.7 so the reader sees there
# is no free-text branch. A tool result maps to exactly one of these.
_ANSWERED = "answered"
_UNAVAILABLE = "unavailable"

# The meter and counter are created lazily on first use, after the MeterProvider
# is installed. Creating them at import time would bind to the no-op provider.
_counter: metrics.Counter | None = None


def _get_counter() -> metrics.Counter:
    global _counter
    if _counter is None:
        meter = metrics.get_meter("tutorial.weather")
        _counter = meter.create_counter(
            "tutorial.weather.requests",
            unit="1",
            description="Weather requests by task outcome (answered vs unavailable).",
        )
    return _counter


def record_outcome(tool, args, tool_context, tool_response) -> None:
    """after_tool_callback: count the tool result as answered or unavailable.

    ADK calls this with (tool, args, tool_context, tool_response). The response
    is the dict the tool returned; its ``status`` decides the outcome. Returning
    None leaves the tool result unchanged -- this callback only observes.
    """
    status = tool_response.get("status") if isinstance(tool_response, dict) else None
    outcome = _ANSWERED if status == "ok" else _UNAVAILABLE
    _get_counter().add(1, {"outcome": outcome})
    return None


def outcome_callbacks() -> list[Any]:
    """The after_tool_callback list, empty unless TUTORIAL_OUTCOME_METRIC is set.

    Splice this into ``Agent(after_tool_callback=...)``: an empty list is the
    same as no callback, so with the flag unset the agent behaves exactly as it
    did through Parts 1 and 2 and emits only the six framework metrics.
    """
    if os.getenv("TUTORIAL_OUTCOME_METRIC"):
        return [record_outcome]
    return []
