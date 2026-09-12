"""Your first datapoint (tutorial 1.1).

Install a metric reader, ask one weather question, and flush. The reader writes
every histogram ADK recorded during the turn to out/metrics.json. Nothing is
recorded without a reader; this script is the smallest thing that makes ADK's
metrics visible.

Run it:

    .venv/bin/python examples/01_console_metrics.py
"""

from __future__ import annotations

import asyncio

from _common import ask, bootstrap, flush_metrics, install_console_reader

bootstrap()

from google.adk.runners import InMemoryRunner  # noqa: E402
from demo_agent.agent import root_agent  # noqa: E402


async def main() -> None:
    install_console_reader()
    runner = InMemoryRunner(agent=root_agent, app_name="metrics_1_1")
    answer = await ask(runner, "What's the weather in London?")
    print("\nAGENT:", answer, "\n")
    # Drain the reader before we exit, or the datapoints never leave the process.
    flush_metrics()


if __name__ == "__main__":
    asyncio.run(main())
