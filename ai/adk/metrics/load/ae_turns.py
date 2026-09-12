#!/usr/bin/env python
"""Fire baseline turns at an agent deployed on Agent Runtime, then wait.

Agent Runtime is not an HTTP server, so ``load/turns.sh`` cannot reach it; turns
go through the Agent Engine SDK instead. This is the 2.5 equivalent of the
baseline scenario: one "What's the weather in London?" turn per fresh session.

The script drives ten turns and then sleeps for the export margin, so the page
can go straight to the Console read-back without a separate wait step. The
request-driven reader flushes as each response completes (see 2.5's deep dive),
so the wait only covers Cloud Monitoring's own aggregation.

It finds the engine the 2.5 deploy created by its display name, so you never copy
the reasoning-engine id by hand. Set RESOURCE to a specific id to override.

Env: PROJECT_ID, REGION; optional RESOURCE, DISPLAY_NAME (default adk-metrics-ae).
"""

from __future__ import annotations

import os
import sys
import time

import vertexai
from vertexai import agent_engines

TURNS = 10
PROMPT = "What's the weather in London?"
WAIT_S = 15
DISPLAY_NAME = os.environ.get("DISPLAY_NAME", "adk-metrics-ae")


def _find_engine():
    """Return the deployed engine, by RESOURCE if set, else by display name."""
    if os.environ.get("RESOURCE"):
        return agent_engines.get(os.environ["RESOURCE"])
    matches = list(agent_engines.list(filter=f'display_name="{DISPLAY_NAME}"'))
    if not matches:
        sys.exit(f"No Agent Engine named {DISPLAY_NAME!r}. Deploy it first (2.5 Step 3).")
    if len(matches) > 1:
        sys.exit(f"{len(matches)} engines named {DISPLAY_NAME!r}; set RESOURCE to pick one.")
    engine = matches[0]
    print(f"using {DISPLAY_NAME}: {engine.resource_name.split('/')[-1]}")
    return engine


def main() -> None:
    vertexai.init(project=os.environ["PROJECT_ID"], location=os.environ["REGION"])
    ae = _find_engine()

    answered = 0
    for i in range(TURNS):
        try:
            session = ae.create_session(user_id="load-user")
            sid = session["id"] if isinstance(session, dict) else session.id
            for _ in ae.stream_query(
                user_id="load-user", session_id=sid, message=PROMPT
            ):
                pass
            answered += 1
            print(f"turn {i + 1} ok")
        except Exception as e:  # a cold engine throws transient FailedPrecondition
            print(f"turn {i + 1} retry ({type(e).__name__})")
            time.sleep(2)

    print(f"answered {answered} of {TURNS}; waiting {WAIT_S}s for export...")
    time.sleep(WAIT_S)


if __name__ == "__main__":
    main()
