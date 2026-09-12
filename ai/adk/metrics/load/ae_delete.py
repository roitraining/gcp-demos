#!/usr/bin/env python
"""Delete the Agent Runtime engine the 2.5 deploy created.

Finds the engine by the display name the deploy set (adk-metrics-ae), so you
never copy the reasoning-engine id by hand. Set RESOURCE to a specific id to
override.

Env: PROJECT_ID, REGION; optional RESOURCE, DISPLAY_NAME (default adk-metrics-ae).
"""

from __future__ import annotations

import os
import sys

import vertexai
from vertexai import agent_engines

DISPLAY_NAME = os.environ.get("DISPLAY_NAME", "adk-metrics-ae")


def main() -> None:
    vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["REGION"])

    if os.environ.get("RESOURCE"):
        engine = agent_engines.get(os.environ["RESOURCE"])
    else:
        matches = list(agent_engines.list(filter=f'display_name="{DISPLAY_NAME}"'))
        if not matches:
            sys.exit(f"No Agent Engine named {DISPLAY_NAME!r}; nothing to delete.")
        if len(matches) > 1:
            sys.exit(f"{len(matches)} engines named {DISPLAY_NAME!r}; set RESOURCE to pick one.")
        engine = matches[0]

    engine.delete(force=True)
    print(f"deleted {engine.resource_name.split('/')[-1]}")


if __name__ == "__main__":
    main()
