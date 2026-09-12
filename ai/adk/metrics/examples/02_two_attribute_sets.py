"""Attributes and cardinality (tutorial 1.3).

Ask two questions in one process: London (a known city) and Atlantis (an unknown
one). ``get_weather`` returns a failure status for Atlantis without raising, so
``gen_ai.execute_tool.duration`` ends the run with two attribute sets, one of
which carries ``error.type``. Same metric, split by what happened.

Run it:

    .venv/bin/python examples/02_two_attribute_sets.py
"""

from __future__ import annotations

import asyncio

from _common import ask, bootstrap, install_inmemory_reader, summarize_series

bootstrap()

from google.adk.runners import InMemoryRunner  # noqa: E402
from demo_agent.agent import root_agent  # noqa: E402


async def main() -> None:
    reader = install_inmemory_reader()
    runner = InMemoryRunner(agent=root_agent, app_name="metrics_1_3")
    for city in ("London", "Atlantis"):
        answer = await ask(runner, f"What's the weather in {city}?")
        print(f"\nAGENT ({city}):", answer)
    print()
    print(summarize_series(reader.get_metrics_data(), "gen_ai.execute_tool.duration"))


if __name__ == "__main__":
    asyncio.run(main())
