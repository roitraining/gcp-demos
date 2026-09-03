"""Example 04: DebugLoggingPlugin, a full-fidelity capture to a YAML file.

Use case
--------
Something went wrong on a specific turn and you want the complete record:
the exact prompt, system instruction, tool arguments, tool results, and
session state, saved to a file you can open, diff, and attach to a bug.

What to notice
--------------
* It writes one YAML document per invocation (``---`` separated) to
  ``adk_debug.yaml`` by default.
* It redacts secrets: credential models, secret-named ``app:``/``user:`` state
  keys, private-key blocks, and everything under ``temp:`` state. The file is
  created readable only by you.
* Because it captures full content, treat the output as sensitive. This is a
  debugging tool, not a production log sink.

Run it
------
    .venv/bin/python examples/04_debug_plugin.py
    cat adk_debug.yaml
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from _common import ask, bootstrap

bootstrap()

from google.adk.apps.app import App
from google.adk.plugins import DebugLoggingPlugin
from google.adk.runners import InMemoryRunner

from demo_agent.agent import root_agent

OUTPUT = Path(__file__).resolve().parent.parent / "adk_debug.yaml"


async def main() -> None:
    plugin = DebugLoggingPlugin(
        output_path=str(OUTPUT),
        include_session_state=True,
        include_system_instruction=True,
    )
    app = App(name="debug_plugin_demo", root_agent=root_agent, plugins=[plugin])
    runner = InMemoryRunner(app=app)

    answer = await ask(runner, "What's the weather in a city you don't know, like Paris?")
    print("FINAL ANSWER:", answer)
    print(f"\nFull invocation captured to: {OUTPUT}")
    print("Open it with:  cat", OUTPUT.name)

    await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
