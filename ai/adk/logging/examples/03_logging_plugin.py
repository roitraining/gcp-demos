"""Example 03: the built-in LoggingPlugin for live terminal debugging.

Use case
--------
You are developing locally and want a running, human-readable narration of
what the agent is doing: which tool was called with which arguments, what the
model returned, token usage per call. You do not want to write any of that
yourself.

What to notice
--------------
* One line wires it up: ``App(..., plugins=[LoggingPlugin()])``.
* The plugin narrates the whole invocation lifecycle with emoji-tagged blocks
  (USER MESSAGE, LLM REQUEST/RESPONSE, TOOL STARTING/COMPLETED, and token usage).
* Caveat worth teaching: LoggingPlugin writes with ``print()`` and ANSI colors,
  NOT through the ``logging`` module. That makes it great for a terminal and a
  poor fit for production log routing. For production, see example 05, which
  emits real ``logging`` records you can format and ship.

Run it
------
    .venv/bin/python examples/03_logging_plugin.py
"""

from __future__ import annotations

import asyncio

from _common import ask, bootstrap

bootstrap()

from google.adk.apps.app import App
from google.adk.plugins import LoggingPlugin
from google.adk.runners import InMemoryRunner

from demo_agent.agent import root_agent


async def main() -> None:
    # Attach the plugin at the App level. This is the ADK 2.x way; passing
    # plugins to Runner still works but is deprecated.
    app = App(name="logging_plugin_demo", root_agent=root_agent, plugins=[LoggingPlugin()])
    runner = InMemoryRunner(app=app)

    answer = await ask(runner, "What's the weather in London?")
    print("\n>>> FINAL ANSWER:", answer)

    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
