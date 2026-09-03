"""Example 01: see what each log level actually shows.

Use case
--------
The log level is the first dial you reach for. Before adding any plugin or
custom config, you should know exactly what DEBUG, INFO, WARNING, and ERROR
each reveal, so you pick the right one instead of drowning in output or flying
blind.

This runs ONE fixed prompt through the shared agent at whatever level you name,
configuring the root logger and the ``google_adk`` group to that level, the same
two things ``adk web --log_level`` does under the hood.

Run it
------
    .venv/bin/python examples/01_log_levels.py info      # the default
    .venv/bin/python examples/01_log_levels.py debug     # full prompt dump
    .venv/bin/python examples/01_log_levels.py warning   # near silence
    .venv/bin/python examples/01_log_levels.py error

Then read the same three-line question at each level and compare.
"""

from __future__ import annotations

import asyncio
import logging
import sys

from _common import ask, bootstrap

bootstrap()

from google.adk.runners import InMemoryRunner

from demo_agent.agent import root_agent

PROMPT = "What's the weather in Tokyo?"


def configure(level_name: str) -> None:
    level = getattr(logging, level_name.upper())
    # This is what `adk web --log_level` does: set the root logger level (which
    # governs your own loggers) and the google_adk group to the same level.
    logging.basicConfig(
        level=level, format="%(levelname)s - %(name)s - %(message)s"
    )
    logging.getLogger("google_adk").setLevel(level)


async def main(level_name: str) -> None:
    configure(level_name)
    print(f"\n===== running at {level_name.upper()} =====\n")
    runner = InMemoryRunner(agent=root_agent, app_name="levels")
    answer = await ask(runner, PROMPT)
    print(f"\n>>> ANSWER: {answer}\n")
    await runner.close()


if __name__ == "__main__":
    level = sys.argv[1] if len(sys.argv) > 1 else "info"
    asyncio.run(main(level))
