"""Reading a histogram (tutorial 1.2).

Ask the same weather question ten times in one process, then draw the recorded
``gen_ai.client.token.usage`` histogram (output tokens) as terminal bars. One
turn puts every value in one bucket; twenty model calls spread across three
buckets, so the shape the metric was recording all along becomes visible.

The bars are drawn from the datapoint's own ``bucket_counts`` and
``explicit_bounds`` -- the same fields the console reader (1.1) prints as JSON.

Run it:

    .venv/bin/python examples/03_histogram_shape.py
"""

from __future__ import annotations

import asyncio
import sys

from _common import (
    ask,
    bootstrap,
    find_datapoint,
    flush_metrics,
    install_inmemory_reader,
    render_histogram,
)

bootstrap()

from google.adk.runners import InMemoryRunner  # noqa: E402
from demo_agent.agent import root_agent  # noqa: E402

TURNS = 10
METRIC = "gen_ai.client.token.usage"


async def main() -> None:
    reader = install_inmemory_reader()
    runner = InMemoryRunner(agent=root_agent, app_name="metrics_1_2")
    for turn in range(1, TURNS + 1):
        print(f"\rasking turn {turn}/{TURNS}...", end="", file=sys.stderr, flush=True)
        await ask(runner, "What's the weather in London?")
    print("\r" + " " * 24 + "\r", end="", file=sys.stderr, flush=True)

    point = find_datapoint(
        reader.get_metrics_data(), METRIC, attr={"gen_ai.token.type": "output"}
    )
    print(f"\n{METRIC}  (output tokens)")
    print(f"count={point.count}  sum={point.sum:.0f}  "
          f"min={point.min:.0f}  max={point.max:.0f}\n")
    print(render_histogram(point))
    print()
    flush_metrics()


if __name__ == "__main__":
    asyncio.run(main())
