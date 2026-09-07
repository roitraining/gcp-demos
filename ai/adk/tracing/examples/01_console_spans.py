"""The raw span tree (tutorial 1.2, 1.4, 1.6).

Install a console span exporter, ask one question, and flush. The exporter
writes every span ADK opened during the turn to out/spans.json. Nothing is
recorded without a provider; this script is the smallest thing that makes ADK's
span tree visible off a laptop.

Run it:

    .venv/bin/python examples/01_console_spans.py
    .venv/bin/python examples/01_console_spans.py "What's the weather in Atlantis?"

The demo agent's env gates (TUTORIAL_CUSTOM_SPAN, TUTORIAL_CLASSIFY_ERRORS,
TUTORIAL_RAISE_ON_UNKNOWN) change the tree without touching this script.
"""

from __future__ import annotations

import asyncio
import sys

from _common import ask, bootstrap, flush_spans, install_console_spans

bootstrap()

from google.adk.runners import InMemoryRunner  # noqa: E402
from demo_agent.agent import root_agent  # noqa: E402


async def main() -> None:
    prompt = sys.argv[1] if len(sys.argv) > 1 else "What's the weather in London?"
    install_console_spans()
    runner = InMemoryRunner(agent=root_agent, app_name="tracing_1")
    try:
        answer = await ask(runner, prompt)
        print("\nAGENT:", answer, "\n")
    finally:
        # Drain before we exit, even if the turn raised (the raised-error gate),
        # or the spans recorded before the raise never leave the process.
        flush_spans()


if __name__ == "__main__":
    asyncio.run(main())
