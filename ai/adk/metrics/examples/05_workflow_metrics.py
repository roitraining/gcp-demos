"""Workflow-grain metrics (tutorial 1.5).

The rest of the tutorial uses a single agent. This example is the one exception:
a two-step SequentialAgent (planner -> weather) so you can see how metrics
attribute themselves when one invocation contains more than one agent.

SequentialAgent is deprecated in favor of the newer Workflow primitive, and only
that newer primitive records gen_ai.invoke_workflow.duration. SequentialAgent is
measured as an outer agent whose duration nests its children, which is the
lesson here. This example stays on SequentialAgent for its simplicity.

Run it:

    .venv/bin/python examples/05_workflow_metrics.py
"""

from __future__ import annotations

import asyncio

from _common import ask, bootstrap, flush_metrics, install_console_reader

bootstrap()

from google.adk.agents import Agent, SequentialAgent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402

from demo_agent.agent import StatusAwareTool, get_weather  # noqa: E402

planner = Agent(
    name="planner",
    model="gemini-3.7-flash",
    instruction="Restate the user's city as: 'Look up weather for <city>.' Nothing else.",
)
weather = Agent(
    name="weather_agent",
    model="gemini-3.7-flash",
    instruction="Call get_weather for the city named and report the result in one sentence.",
    tools=[StatusAwareTool(get_weather)],
)
workflow = SequentialAgent(name="weather_workflow", sub_agents=[planner, weather])


async def main() -> None:
    install_console_reader()
    runner = InMemoryRunner(agent=workflow, app_name="metrics_1_5")
    answer = await ask(runner, "What's the weather in London?")
    print("\nAGENT:", answer, "\n")
    flush_metrics()


if __name__ == "__main__":
    asyncio.run(main())
